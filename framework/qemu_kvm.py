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


import time
import re
import os

from virt_base import VirtBase
from virt_base import ST_NOTSTART, ST_PAUSE, ST_RUNNING, ST_UNKNOWN
from exception import StartVMFailedException
from settings import get_host_ip, load_global_setting, DTS_PARALLEL_SETTING
from utils import parallel_lock, RED

# This name is directly defined in the qemu guest service
# So you can not change it except it is changed by the service
QGA_DEV_NAME = 'org.qemu.guest_agent.0'


class QEMUKvm(VirtBase):

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
    # Default login session timeout value
    LOGIN_TIMEOUT = 60
    # By default will wait 120 seconds for VM start
    # If VM not ready in this period, will try restart it once
    START_TIMEOUT = 120
    # Default timeout value for operation when VM starting
    OPERATION_TIMEOUT = 20
    # Default login prompt
    LOGIN_PROMPT = "login:"
    # Default password prompt
    PASSWORD_PROMPT = "Password:"

    def __init__(self, dut, vm_name, suite_name):
        super(QEMUKvm, self).__init__(dut, vm_name, suite_name)

        # initialize qemu emulator, example: qemu-system-x86_64
        self.qemu_emulator = self.get_qemu_emulator()

        # initialize qemu boot command line
        # example: qemu-system-x86_64 -name vm1 -m 2048 -vnc :1 -daemonize
        self.qemu_boot_line = ''

        # initialize some resource used by guest.
        self.init_vm_request_resource()

        # character and network device default index
        self.char_idx = 0
        self.netdev_idx = 0
        self.pt_idx = 0
        self.cuse_id = 0
        # devices pass-through into vm
        self.pt_devices = []
        self.pci_maps = []

        # default login user,password
        self.username = dut.crb['user']
        self.password = dut.crb['pass']

        # internal variable to track whether default nic has been added
        self.__default_nic = False

        # arch info for multi-platform init
        self.arch = self.host_session.send_expect('uname -m', '# ')

        # set some default values for vm,
        # if there is not the values of the specified options
        self.set_vm_default()

        self.am_attached = False

        # allow restart VM when can't login
        self.restarted = False

    def check_alive(self):
        """
        Check whether VM is alive for has been start up
        """
        pid_regx = r'p(\d+)'
        out = self.host_session.send_expect("lsof -Fp /tmp/.%s.pid" % self.vm_name, "#", timeout=30)
        for line in out.splitlines():
            m = re.match(pid_regx, line)
            if m:
                self.host_logger.info("Found VM %s already running..." % m.group(0))
                return True
        return False

    def kill_alive(self):
        pid_regx = r'p(\d+)'
        out = self.host_session.send_expect("lsof -Fp /tmp/.%s.pid" % self.vm_name, "# ")
        for line in out.splitlines():
            m = re.match(pid_regx, line)
            if m:
                self.host_session.send_expect("kill -9 %s" % m.group(0)[1:], "# ")

    def set_vm_default(self):
        self.set_vm_name(self.vm_name)
        if self.arch == 'aarch64':
            self.set_vm_machine('virt')
        self.set_vm_enable_kvm()
        self.set_vm_pid_file()
        self.set_vm_daemon()
        self.set_vm_monitor()

        self.nic_num = 1
        if not self.__default_nic:
            # add default control interface
            def_nic = {'type': 'nic'}
            self.set_vm_net(**def_nic)
            def_net = {'type': 'user'}
            self.set_vm_net(**def_net)
            self.__default_nic = True

    def init_vm_request_resource(self):
        """
        initialize some resource used by VM.
        examples: CPU, PCIs, so on.
        CPU:
        initialize vcpus what will be pinned to the VM.
        If specify this param, the specified vcpus will
        be pinned to VM by the command 'taskset' when
        starting the VM.
        example:
            vcpus_pinned_to_vm = '1 2 3 4'
            taskset -c 1,2,3,4 qemu-boot-command-line
        """
        self.vcpus_pinned_to_vm = ''

        # initialize assigned PCI
        self.assigned_pcis = []

    def get_virt_type(self):
        """
        Get the virtual type.
        """
        return 'KVM'

    def get_qemu_emulator(self):
        """
        Get the qemu emulator based on the crb.
        """
        arch = self.host_session.send_expect('uname -m', '# ')
        return 'qemu-system-' + arch

    def set_qemu_emulator(self, qemu_emulator_path):
        """
        Set the qemu emulator in the specified path explicitly.
        """
        out = self.host_session.send_expect(
            'ls %s' % qemu_emulator_path, '# ')
        if 'No such file or directory' in out:
            self.host_logger.error("No emulator [ %s ] on the DUT [ %s ]" %
                                   (qemu_emulator_path, self.host_dut.get_ip_address()))
            return None
        out = self.host_session.send_expect(
            "[ -x %s ];echo $?" % qemu_emulator_path, '# ')
        if out != '0':
            self.host_logger.error(
                "Emulator [ %s ] not executable on the DUT [ %s ]" %
                                   (qemu_emulator_path, self.host_dut.get_ip_address()))
            return None
        self.qemu_emulator = qemu_emulator_path

    def add_vm_qemu(self, **options):
        """
        path: absolute path for qemu emulator
        """
        if 'path' in list(options.keys()):
            self.set_qemu_emulator(options['path'])

    def has_virtual_ability(self):
        """
        Check if host has the virtual ability.
        """
        out = self.host_session.send_expect(
            'cat /proc/cpuinfo | grep flags', '# ')
        rgx = re.search(' vmx ', out)
        if rgx:
            pass
        else:
            self.host_logger.warning(
                "Hardware virtualization disabled on host!!!")
            return False

        out = self.host_session.send_expect('lsmod | grep kvm', '# ')
        if 'kvm' in out and 'kvm_intel' in out:
            return True
        else:
            self.host_logger.warning("kvm or kvm_intel not insmod!!!")
            return False

    def enable_virtual_ability(self):
        """
        Load the virtual module of kernel to enable the virtual ability.
        """
        self.host_session.send_expect('modprobe kvm', '# ')
        self.host_session.send_expect('modprobe kvm_intel', '# ')
        return True

    def disk_image_is_ok(self, image):
        """
        Check if the image is OK and no error.
        """
        pass

    def image_is_used(self, image_path):
        """
        Check if the image has been used on the host.
        """
        qemu_cmd_lines = self.host_session.send_expect(
            "ps aux | grep qemu | grep -v grep", "# ")

        image_name_flag = '/' + image_path.strip().split('/')[-1] + ' '
        if image_path in qemu_cmd_lines or \
                image_name_flag in qemu_cmd_lines:
            return True
        return False

    def __add_boot_line(self, option_boot_line):
        """
        Add boot option into the boot line.
        """
        separator = ' '
        self.qemu_boot_line += separator + option_boot_line

    def set_vm_enable_kvm(self, enable='yes'):
        """
        Set VM boot option to enable the option 'enable-kvm'.
        """
        index = self.find_option_index('enable_kvm')
        if index:
            self.params[index] = {'enable_kvm': [{'enable': '%s' % enable}]}
        else:
            self.params.append({'enable_kvm': [{'enable': '%s' % enable}]})

    def add_vm_enable_kvm(self, **options):
        """
        'enable': 'yes'
        """
        if 'enable' in list(options.keys()) and \
                options['enable'] == 'yes':
            enable_kvm_boot_line = '-enable-kvm'
            self.__add_boot_line(enable_kvm_boot_line)

    def set_vm_machine(self, machine):
        """
        Set VM boot option to specify the option 'machine'.
        """
        index = self.find_option_index('machine')
        if index:
            self.params[index] = {'machine': [{'machine': '%s' % machine}]}
        else:
            self.params.append({'machine': [{'machine': '%s' % machine}]})

    def add_vm_machine(self, **options):
        """
        'machine': 'virt','opt_gic_version'
        """
        machine_boot_line='-machine'
        separator = ','
        if 'machine' in list(options.keys()) and \
                options['machine']:
            machine_boot_line += ' %s' % options['machine']
            if 'opt_gic_version' in list(options.keys()) and \
                    options['opt_gic_version']:
                machine_boot_line += separator + 'gic_version=%s' % options['opt_gic_version']

            self.__add_boot_line(machine_boot_line)

    def set_vm_pid_file(self):
        """
        Set VM pidfile option for manage qemu process
        """
        self.__pid_file = '/tmp/.%s.pid' % self.vm_name
        index = self.find_option_index('pid_file')
        if index:
            self.params[index] = {
                'pid_file': [{'name': '%s' % self.__pid_file}]}
        else:
            self.params.append(
                {'pid_file': [{'name': '%s' % self.__pid_file}]})

    def add_vm_pid_file(self, **options):
        """
        'name' : '/tmp/.qemu_vm0.pid'
        """
        if 'name' in list(options.keys()):
            self.__add_boot_line('-pidfile %s' % options['name'])

    def set_vm_name(self, vm_name):
        """
        Set VM name.
        """
        index = self.find_option_index('name')
        if index:
            self.params[index] = {'name': [{'name': '%s' % vm_name}]}
        else:
            self.params.append({'name': [{'name': '%s' % vm_name}]})

    def add_vm_name(self, **options):
        """
        name: vm1
        """
        if 'name' in list(options.keys()) and \
                options['name']:
            name_boot_line = '-name %s' % options['name']
            self.__add_boot_line(name_boot_line)

    def add_vm_cpu(self, **options):
        """
        model: [host | core2duo | ...]
               usage:
                    choose model value from the command
                        qemu-system-x86_64 -cpu help
        number: '4' #number of vcpus
        cpupin: '3 4 5 6' # host cpu list
        """
        if 'model' in list(options.keys()) and \
                options['model']:
            cpu_boot_line = '-cpu %s' % options['model']
            self.__add_boot_line(cpu_boot_line)
        if 'number' in list(options.keys()) and \
                options['number']:
            smp_cmd_line = '-smp %d' % int(options['number'])
            self.__add_boot_line(smp_cmd_line)
        if 'cpupin' in list(options.keys()) and \
                options['cpupin']:
            self.vcpus_pinned_to_vm = str(options['cpupin'])

    def add_vm_mem(self, **options):
        """
        size: 1024
        """
        if 'size' in list(options.keys()):
            mem_boot_line = '-m %s' % options['size']
            self.__add_boot_line(mem_boot_line)
        if 'hugepage' in list(options.keys()):
            if options['hugepage'] == 'yes':
                mem_boot_huge = '-object memory-backend-file,' \
                                + 'id=mem,size=%sM,mem-path=%s,share=on' \
                                % (options['size'], self.host_dut.hugepage_path)

                self.__add_boot_line(mem_boot_huge)
                mem_boot_huge_opt = "-numa node,memdev=mem -mem-prealloc"
                self.__add_boot_line(mem_boot_huge_opt)

    def add_vm_disk(self, **options):
        """
        file: /home/image/test.img
        opt_format: raw
        opt_if: virtio
        opt_index: 0
        opt_media: disk
        """
        separator = ','
        if 'file' in list(options.keys()) and \
                options['file']:
            disk_boot_line = '-drive file=%s' % options['file']
        else:
            return False

        if 'opt_format' in list(options.keys()) and \
                options['opt_format']:
            disk_boot_line += separator + 'format=%s' % options['opt_format']
        if 'opt_if' in list(options.keys()) and \
                options['opt_if']:
            disk_boot_line += separator + 'if=%s' % options['opt_if']
        if 'opt_index' in list(options.keys()) and \
                options['opt_index']:
            disk_boot_line += separator + 'index=%s' % options['opt_index']
        if 'opt_media' in list(options.keys()) and \
                options['opt_media']:
            disk_boot_line += separator + 'media=%s' % options['opt_media']

        self.__add_boot_line(disk_boot_line)

    def add_vm_pflash(self, **options):
        """
        file: /home/image/flash0.img
        """
        if 'file' in list(options.keys()):
            pflash_boot_line = '-pflash %s' % options['file']
            self.__add_boot_line(pflash_boot_line)

    def add_vm_start(self, **options):
        """
        Update VM start and login related settings
        """
        if 'wait_seconds' in list(options.keys()):
            self.START_TIMEOUT = int(options['wait_seconds'])
        if 'login_timeout' in list(options.keys()):
            self.LOGIN_TIMEOUT = int(options['login_timeout'])
        if 'login_prompt' in list(options.keys()):
            self.LOGIN_PROMPT = options['login_prompt']
        if 'password_prompt' in list(options.keys()):
            self.PASSWORD_PROMPT = options['password_prompt']

    def add_vm_login(self, **options):
        """
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

    def set_vm_net(self, **options):
        index = self.find_option_index('net')
        if index:
            self.params[index]['net'].append(options)
        else:
            self.params.append({'net': [options]})

    def add_vm_net(self, **options):
        """
        Add VM net device.
        type: [nic | user | tap | bridge | ...]
        opt_[vlan | fd | br | mac | ...]
            note:the sub-option will be decided according to the net type.
        """
        if 'type' in list(options.keys()):
            if options['type'] == 'nic':
                self.__add_vm_net_nic(**options)
            if options['type'] == 'user':
                self.__add_vm_net_user(**options)
            if options['type'] == 'tap':
                self.__add_vm_net_tap(**options)

            if options['type'] == 'user':
                self.net_type = 'hostfwd'
            elif options['type'] in ['tap', 'bridge']:
                self.net_type = 'bridge'

    def add_vm_kernel(self, **options):
        """
        Add Kernel Image explicitly
        kernel_img: path to kernel Image
        console: console details in kernel boot args
        baudrate: console access baudrate in kernel boot args
        root: root partition details in kernel boot args
        """
        print(options)
        if 'kernel_img' in list(options.keys()) and options['kernel_img']:
            kernel_boot_line = '-kernel %s' % options['kernel_img']
        else:
            return False
        self.__add_boot_line(kernel_boot_line)
        kernel_args = ""
        if 'console' in list(options.keys()) and options['console']:
            kernel_args = "console=%s" %options['console']
            if 'baudrate' in list(options.keys()) and options['baudrate']:
                kernel_args += "," + options['baudrate']
        if 'root' in list(options.keys()) and options['root']:
            kernel_args += " root=%s" %options['root']
        if kernel_args:
            append_boot_line = '--append \"%s\"' %kernel_args
            self.__add_boot_line(append_boot_line)

    def __add_vm_net_nic(self, **options):
        """
        type: nic
        opt_model:["e1000" | "virtio" | "i82551" | ...]
            note: Default is e1000.
        """
        net_boot_line = '-device '
        separator = ','

        if 'opt_model' in list(options.keys()) and \
                options['opt_model']:
            model = options['opt_model']
        else:
            model = 'e1000'
        self.nic_model = model
        net_boot_line += model

        netdev_id = self.nic_num
        if self.nic_num % 2 == 0:
            netdev_id = self.nic_num - 1
        netdev = "netdev=nttsip%d " % netdev_id
        self.nic_num = self.nic_num + 1
        net_boot_line += separator + netdev

        if self.__string_has_multi_fields(net_boot_line, separator):
            self.__add_boot_line(net_boot_line)

    def __add_vm_net_user(self, **options):
        """
        type: user
        opt_hostfwd: [tcp|udp]:[hostaddr]:hostport-[guestaddr]:guestport
        """
        net_boot_line = '-netdev user'
        separator = ','
        netdev_id = self.nic_num
        if self.nic_num % 2 == 0:
            netdev_id = self.nic_num - 1
        self.nic_num = self.nic_num + 1
        netdev = "id=nttsip%d" % netdev_id
        net_boot_line += separator + netdev
        if 'opt_hostfwd' in list(options.keys()) and \
                options['opt_hostfwd']:
            self.__check_net_user_opt_hostfwd(options['opt_hostfwd'])
            opt_hostfwd = options['opt_hostfwd']
        else:
            opt_hostfwd = '::-:'
        hostfwd_line = self.__parse_net_user_opt_hostfwd(opt_hostfwd)
        net_boot_line += separator + 'hostfwd=%s' % hostfwd_line

        if self.__string_has_multi_fields(net_boot_line, separator):
            self.__add_boot_line(net_boot_line)

    def __check_net_user_opt_hostfwd(self, opt_hostfwd):
        """
        Use regular expression to check if hostfwd value format is correct.
        """
        regx_ip = '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
        regx_hostfwd = r'(tcp|udp)?:(%s)?:\d+-(%s)?:\d+' % (regx_ip, regx_ip)
        if not re.match(regx_hostfwd, opt_hostfwd):
            raise Exception("Option opt_hostfwd format is not correct,\n" +
                            "it is %s,\n " % opt_hostfwd +
                            "it should be [tcp|udp]:[hostaddr]:hostport-" +
                            "[guestaddr]:guestport.\n")

    def __parse_net_user_opt_hostfwd(self, opt_hostfwd):
        """
        Parse the boot option 'hostfwd'.
        """
        separator = ':'
        field = lambda option, index, separator=':': \
            option.split(separator)[index]

        # get the forward type
        fwd_type = field(opt_hostfwd, 0)
        if not fwd_type:
            fwd_type = 'tcp'

        # get the host addr
        host_addr = field(opt_hostfwd, 1)
        if not host_addr:
            addr = str(self.host_dut.get_ip_address())
            host_addr = get_host_ip(addr)

        # get the host port in the option
        host_port = field(opt_hostfwd, 2).split('-')[0]

        # if no host assigned, just allocate it
        if not host_port:
            host_port = str(self.virt_pool.alloc_port(self.vm_name, port_type='connect'))

        self.redir_port = host_port

        # get the guest addr
        try:
            guest_addr = str(field(opt_hostfwd, 2).split('-')[1])
        except IndexError as e:
            guest_addr = ''

        # get the guest port in the option
        guest_port = str(field(opt_hostfwd, 3))
        if not guest_port:
            guest_port = '22'

        hostfwd_line = fwd_type + separator + \
            host_addr + separator + \
            host_port + \
            '-' + \
            guest_addr + separator + \
            guest_port

        # init the redirect incoming TCP or UDP connections
        # just combine host address and host port, it is enough
        # for using ssh to connect with VM
        self.hostfwd_addr = host_addr + separator + host_port

        return hostfwd_line

    def __add_vm_net_tap(self, **options):
        """
        type: tap
        opt_br: br0
            note: if choosing tap, need to specify bridge name,
                  else it will be br0.
        opt_script: QEMU_IFUP_PATH
            note: if not specified, default is self.QEMU_IFUP_PATH.
        opt_downscript: QEMU_IFDOWN_PATH
            note: if not specified, default is self.QEMU_IFDOWN_PATH.
        """
        net_boot_line = '-netdev tap'
        separator = ','

        netdev_id = self.nic_num
        if self.nic_num % 2 == 0:
            netdev_id = self.nic_num - 1
        self.nic_num = self.nic_num + 1
        netdev = "id=nttsip%d" % netdev_id
        net_boot_line += separator + netdev

        # add bridge info
        if 'opt_br' in list(options.keys()) and \
                options['opt_br']:
            bridge = options['opt_br']
        else:
            bridge = self.DEFAULT_BRIDGE
        self.__generate_net_config_script(str(bridge))

        # add network configure script path
        if 'opt_script' in list(options.keys()) and \
                options['opt_script']:
            script_path = options['opt_script']
        else:
            script_path = self.QEMU_IFUP_PATH
        net_boot_line += separator + 'script=%s' % script_path

        # add network configure downscript path
        if 'opt_downscript' in list(options.keys()) and \
                options['opt_downscript']:
            net_boot_line += separator + \
                'downscript=%s' % options['opt_downscript']

        if self.__string_has_multi_fields(net_boot_line, separator):
            self.__add_boot_line(net_boot_line)

    def __generate_net_config_script(self, switch=DEFAULT_BRIDGE):
        """
        Generate a script for qemu emulator to build a tap device
        between host and guest.
        """
        qemu_ifup = self.QEMU_IFUP % {'switch': switch}
        file_name = os.path.basename(self.QEMU_IFUP_PATH)
        tmp_file_path = '/tmp/%s' % file_name
        self.host_dut.create_file(qemu_ifup, tmp_file_path)
        self.host_session.send_expect('mv -f ~/%s %s' % (file_name,
                                                         self.QEMU_IFUP_PATH), '# ')
        self.host_session.send_expect(
            'chmod +x %s' % self.QEMU_IFUP_PATH, '# ')

    def set_vm_device(self, driver='pci-assign', **opts):
        """
        Set VM device with specified driver.
        """
        opts['driver'] = driver
        index = self.find_option_index('device')
        if index:
            self.params[index]['device'].append(opts)
        else:
            self.params.append({'device': [opts]})

        # start up time may increase after add device
        self.START_TIMEOUT += 8

    def add_vm_device(self, **options):
        """
        driver: [pci-assign | virtio-net-pci | ...]
        opt_[host | addr | ...]: value
            note:the sub-option will be decided according to the driver.
        """
        if 'driver' in list(options.keys()) and \
                options['driver']:
            if options['driver'] == 'pci-assign':
                self.__add_vm_pci_assign(**options)
            elif options['driver'] == 'virtio-net-pci':
                self.__add_vm_virtio_net_pci(**options)
            elif options['driver'] == 'vhost-user':
                self.__add_vm_virtio_user_pci(**options)
            elif options['driver'] == 'vhost-cuse':
                self.__add_vm_virtio_cuse_pci(**options)
            elif options['driver'] == 'vfio-pci':
                 self.__add_vm_pci_vfio(**options)

    def __add_vm_pci_vfio(self, **options):
        """
        driver: vfio-pci
        opt_host: 08:00.0
        opt_addr: 00:00:00:00:01:02
        """
        dev_boot_line = '-device vfio-pci'
        separator = ','
        if 'opt_host' in list(options.keys()) and \
                options['opt_host']:
            dev_boot_line += separator + 'host=%s' % options['opt_host']
            dev_boot_line += separator + 'id=pt_%d' % self.pt_idx
            self.pt_idx += 1
            self.pt_devices.append(options['opt_host'])
        if 'opt_addr' in list(options.keys()) and \
                options['opt_addr']:
            dev_boot_line += separator + 'addr=%s' % options['opt_addr']
            self.assigned_pcis.append(options['opt_addr'])

        if self.__string_has_multi_fields(dev_boot_line, separator):
            self.__add_boot_line(dev_boot_line)

    def __add_vm_pci_assign(self, **options):
        """
        driver: pci-assign
        opt_host: 08:00.0
        opt_addr: 00:00:00:00:01:02
        """
        dev_boot_line = '-device pci-assign'
        separator = ','
        if 'opt_host' in list(options.keys()) and \
                options['opt_host']:
            dev_boot_line += separator + 'host=%s' % options['opt_host']
            dev_boot_line += separator + 'id=pt_%d' % self.pt_idx
            self.pt_idx += 1
            self.pt_devices.append(options['opt_host'])
        if 'opt_addr' in list(options.keys()) and \
                options['opt_addr']:
            dev_boot_line += separator + 'addr=%s' % options['opt_addr']
            self.assigned_pcis.append(options['opt_addr'])

        if self.__string_has_multi_fields(dev_boot_line, separator):
            self.__add_boot_line(dev_boot_line)

    def __add_vm_virtio_user_pci(self, **options):
        """
        driver virtio-net-pci
        opt_path: /tmp/vhost-net
        opt_mac: 00:00:20:00:00:00
        """
        separator = ','
        # chardev parameter
        netdev_id = 'netdev%d' % self.netdev_idx
        if 'opt_script' in list(options.keys()) and options['opt_script']:
            if 'opt_br' in list(options.keys()) and \
                    options['opt_br']:
                bridge = options['opt_br']
            else:
                bridge = self.DEFAULT_BRIDGE
            self.__generate_net_config_script(str(bridge))
            dev_boot_line = '-netdev tap,id=%s,script=%s' % (netdev_id, options['opt_script'])
            self.netdev_idx += 1
        elif 'opt_path' in list(options.keys()) and options['opt_path']:
            dev_boot_line = '-chardev socket'
            char_id = 'char%d' % self.char_idx
            if 'opt_server' in list(options.keys()) and options['opt_server']:
                dev_boot_line += separator + 'id=%s' % char_id + separator + \
                    'path=%s' % options[
                        'opt_path'] + separator + '%s' % options['opt_server']
                self.char_idx += 1
                self.__add_boot_line(dev_boot_line)
            else:
                dev_boot_line += separator + 'id=%s' % char_id + \
                    separator + 'path=%s' % options['opt_path']
                self.char_idx += 1
                self.__add_boot_line(dev_boot_line)
            # netdev parameter
            netdev_id = 'netdev%d' % self.netdev_idx
            self.netdev_idx += 1
            if 'opt_queue' in list(options.keys()) and options['opt_queue']:
                queue_num = options['opt_queue']
                dev_boot_line = '-netdev type=vhost-user,id=%s,chardev=%s,vhostforce,queues=%s' % (
                    netdev_id, char_id, queue_num)
            else:
                dev_boot_line = '-netdev type=vhost-user,id=%s,chardev=%s,vhostforce' % (
                    netdev_id, char_id)
            self.__add_boot_line(dev_boot_line)
            # device parameter
        opts = {'opt_netdev': '%s' % netdev_id}
        if 'opt_mac' in list(options.keys()) and \
                options['opt_mac']:
            opts['opt_mac'] = options['opt_mac']
        if 'opt_settings' in list(options.keys()) and options['opt_settings']:
            opts['opt_settings'] = options['opt_settings']
        if 'opt_legacy' in list(options.keys()) and options['opt_legacy']:
            opts['opt_legacy'] = options['opt_legacy']
        self.__add_vm_virtio_net_pci(**opts)

    def __add_vm_virtio_cuse_pci(self, **options):
        """
        driver virtio-net-pci
        opt_mac: 52:54:00:00:00:01
        """
        separator = ','
        dev_boot_line = '-netdev tap'
        if 'opt_tap' in list(options.keys()):
            cuse_id = options['opt_tap']
        else:
            cuse_id = 'vhost%d' % self.cuse_id
            self.cuse_id += 1
        dev_boot_line += separator + 'id=%s' % cuse_id + separator + \
            'ifname=tap_%s' % cuse_id + separator + \
            "vhost=on" + separator + "script=no"
        self.__add_boot_line(dev_boot_line)
        # device parameter
        opts = {'opt_netdev': '%s' % cuse_id,
                'opt_id': '%s_net' % cuse_id}
        if 'opt_mac' in list(options.keys()) and options['opt_mac']:
            opts['opt_mac'] = options['opt_mac']
        if 'opt_settings' in list(options.keys()) and options['opt_settings']:
            opts['opt_settings'] = options['opt_settings']

        self.__add_vm_virtio_net_pci(**opts)

    def __add_vm_virtio_net_pci(self, **options):
        """
        driver: virtio-net-pci
        opt_netdev: mynet1
        opt_id: net1
        opt_mac: 00:00:00:00:01:03
        opt_bus: pci.0
        opt_addr: 0x3
        opt_settings: csum=off,gso=off,guest_csum=off
        """
        dev_boot_line = '-device virtio-net-pci'
        separator = ','
        if 'opt_netdev' in list(options.keys()) and \
                options['opt_netdev']:
            dev_boot_line += separator + 'netdev=%s' % options['opt_netdev']
        if 'opt_id' in list(options.keys()) and \
                options['opt_id']:
            dev_boot_line += separator + 'id=%s' % options['opt_id']
        if 'opt_mac' in list(options.keys()) and \
                options['opt_mac']:
            dev_boot_line += separator + 'mac=%s' % options['opt_mac']
        if 'opt_bus' in list(options.keys()) and \
                options['opt_bus']:
            dev_boot_line += separator + 'bus=%s' % options['opt_bus']
        if 'opt_addr' in list(options.keys()) and \
                options['opt_addr']:
            dev_boot_line += separator + 'addr=%s' % options['opt_addr']
        if 'opt_legacy' in list(options.keys()) and \
                options['opt_legacy']:
            dev_boot_line += separator + 'disable-modern=%s' % options['opt_legacy']
        if 'opt_settings' in list(options.keys()) and \
                options['opt_settings']:
            dev_boot_line += separator + '%s' % options['opt_settings']

        if self.__string_has_multi_fields(dev_boot_line, separator):
            self.__add_boot_line(dev_boot_line)

    def __string_has_multi_fields(self, string, separator, field_num=2):
        """
        Check if string has multiple fields which are splitted with
        specified separator.
        """
        fields = string.split(separator)
        number = 0
        for field in fields:
            if field:
                number += 1
        if number >= field_num:
            return True
        else:
            return False

    def set_vm_monitor(self):
        """
        Set VM boot option to enable qemu monitor.
        """
        index = self.find_option_index('monitor')
        if index:
            self.params[index] = {'monitor': [{'path': '/tmp/%s_monitor.sock' %
                                              (self.vm_name)}]}
        else:
            self.params.append({'monitor': [{'path': '/tmp/%s_monitor.sock' %
                               (self.vm_name)}]})

    def add_vm_monitor(self, **options):
        """
        path: if adding monitor to vm, need to specify unix socket path
        """
        if 'path' in list(options.keys()):
            monitor_boot_line = '-monitor unix:%s,server,nowait' % options[
                'path']
            self.__add_boot_line(monitor_boot_line)
            self.monitor_sock_path = options['path']
        else:
            self.monitor_sock_path = None

    def add_vm_migration(self, **options):
        """
        enable: yes
        port: tcp port for live migration
        """
        migrate_cmd = "-incoming tcp::%(migrate_port)s"

        if 'enable' in list(options.keys()):
            if options['enable'] == 'yes':
                if 'port' in list(options.keys()):
                    self.migrate_port = options['port']
                else:
                    self.migrate_port = str(
                        self.virt_pool.alloc_port(self.vm_name), port_type="migrate")
                migrate_boot_line = migrate_cmd % {
                    'migrate_port': self.migrate_port}
                self.__add_boot_line(migrate_boot_line)


    def set_vm_control(self, **options):
        """
        Set control session options
        """
        if 'type' in  list(options.keys()):
            self.control_type = options['type']
        else:
            self.control_type = 'telnet'

        index = self.find_option_index('control')
        if index:
            self.params[index] = {'control': [{'type': self.control_type}]}
        else:
            self.params.append({'control': [{'type': self.control_type}]})

    def add_vm_control(self, **options):
        """
        Add control method for VM management
        type : 'telnet' | 'socket' | 'qga'
        """
        separator = ' '

        self.control_type = options['type']
        if self.control_type == 'telnet':
            if 'port' in options:
                self.serial_port = int(options['port'])
            else:
                self.serial_port = self.virt_pool.alloc_port(self.vm_name, port_type="serial")
            control_boot_line = '-serial telnet::%d,server,nowait' % self.serial_port
        elif self.control_type == 'socket':
            self.serial_path = "/tmp/%s_serial.sock" % self.vm_name
            control_boot_line = '-serial unix:%s,server,nowait' % self.serial_path
        elif self.control_type == 'qga':
            qga_dev_id = '%(vm_name)s_qga0' % {'vm_name': self.vm_name}
            self.qga_socket_path = '/tmp/%(vm_name)s_qga0.sock' % {'vm_name': self.vm_name}
            self.qga_cmd_head = '~/QMP/qemu-ga-client --address=%s ' % self.qga_socket_path
            qga_boot_block = '-chardev socket,path=%(SOCK_PATH)s,server,nowait,id=%(ID)s' + \
                  separator + '-device virtio-serial' + separator + \
                  '-device virtserialport,chardev=%(ID)s,name=%(DEV_NAME)s'
            control_boot_line = qga_boot_block % {'SOCK_PATH': self.qga_socket_path,
                                              'DEV_NAME': QGA_DEV_NAME,
                                              'ID': qga_dev_id}

        self.__add_boot_line(control_boot_line)

    def connect_serial_port(self, name=""):
        """
        Connect to serial port and return connected session for usage
        if connected failed will return None
        """
        shell_reg = r"(.*)# "
        try:
            if getattr(self, 'control_session', None) is None:
                self.control_session = self.host_session

                self.control_session.send_command("socat %s STDIO" % self.serial_path)

            # login message not output if timeout is too small
            out = self.control_session.send_command("", timeout=5).replace('\r', '').replace('\n', '')

            if len(out) == 0:
                raise StartVMFailedException("Can't get output from [%s:%s]" % (self.host_dut.crb['My IP'], self.vm_name))

            m = re.match(shell_reg, out)
            if m:
                # dmidecode output contain #, so use other matched string
                out = self.control_session.send_expect("dmidecode -t system", "Product Name", timeout=self.OPERATION_TIMEOUT)
                # cleanup previous output
                self.control_session.get_session_before(timeout=0.1)

                # if still on host, need reconnect
                if 'QEMU' not in out:
                    raise StartVMFailedException("Not real login [%s]" % self.vm_name)
                else:
                    # has enter into VM shell
                    return True

            # login into Redhat os, not sure can work on all distributions
            if self.LOGIN_PROMPT not in out:
                raise StartVMFailedException("Can't login [%s] now!!!" % self.vm_name)
            else:
                self.control_session.send_expect("%s" % self.username, self.PASSWORD_PROMPT, timeout=self.LOGIN_TIMEOUT)
                # system maybe busy here, enlarge timeout equal to login timeout
                self.control_session.send_expect("%s" % self.password, "#", timeout=self.LOGIN_TIMEOUT)
                return self.control_session
        except Exception as e:
            # when exception happened, force close serial connection and reconnect
            print(RED("[%s:%s] exception [%s] happened" % (self.host_dut.crb['My IP'], self.vm_name, str(e))))
            self.close_control_session(dut_id=self.host_dut.dut_id)
            return False

    def connect_telnet_port(self, name=""):
        """
        Connect to serial port and return connected session for usage
        if connected failed will return None
        """
        shell_reg = r"(.*)# "
        scan_cmd = "lsof -i:%d | grep telnet | awk '{print $2}'" % self.serial_port

        try:
            # assume serial is not connect
            if getattr(self, 'control_session', None) is None:
                self.control_session = self.host_session

                self.control_session.send_expect("telnet localhost %d" % self.serial_port, "Connected to localhost", timeout=self.OPERATION_TIMEOUT)

            # output will be empty if timeout too small
            out = self.control_session.send_command("", timeout=5).replace('\r', '').replace('\n', '')

            # if no output from serial port, either connection close or system hang
            if len(out) == 0:
                raise StartVMFailedException("Can't get output from [%s]" % self.vm_name)

            # if enter into shell
            m = re.match(shell_reg, out)
            if m:
                # dmidecode output contain #, so use other matched string
                out = self.control_session.send_expect("dmidecode -t system", "Product Name", timeout=self.OPERATION_TIMEOUT)
                # cleanup previous output
                self.control_session.get_session_before(timeout=0.1)

                # if still on host, need reconnect
                if 'QEMU' not in out:
                    raise StartVMFailedException("Not real login [%s]" % self.vm_name)
                else:
                    # has enter into VM shell
                    return True

            # login into Redhat os, not sure can work on all distributions
            if ("x86_64 on an x86_64" not in out) and (self.LOGIN_PROMPT not in out):
                print(RED("[%s:%s] not ready for login" % (self.host_dut.crb['My IP'], self.vm_name)))
                return False
            else:
                self.control_session.send_expect("%s" % self.username, "Password:", timeout=self.LOGIN_TIMEOUT)
                self.control_session.send_expect("%s" % self.password, "#", timeout=self.LOGIN_TIMEOUT)
                return True
        except Exception as e:
            # when exception happened, force close serial connection and reconnect
            print(RED("[%s:%s] exception [%s] happened" % (self.host_dut.crb['My IP'], self.vm_name, str(e))))
            self.close_control_session(dut_id=self.host_dut.dut_id)
            return False

    def connect_qga_port(self, name=""):
        """
        QGA control session just share with host session
        """
        try:
            # assume serial is not connect
            if getattr(self, 'control_session', None) is None:
                self.control_session = self.host_session

            self.control_session.send_expect("%s ping %d" %(self.qga_cmd_head, self.START_TIMEOUT), "#", timeout=self.START_TIMEOUT)

            # here VM has been start and qga also ready
            return True
        except Exception as e:
            # when exception happened, force close qga process and reconnect
            print(RED("[%s:%s] QGA not ready" % (self.host_dut.crb['My IP'], self.vm_name)))
            self.close_control_session(dut_id=self.host_dut.dut_id)
            return False

    def add_vm_vnc(self, **options):
        """
        Add VM display option
        """
        if 'disable' in list(options.keys()) and options['disable'] == 'True':
            vnc_boot_line = '-display none'
        else:
            if 'displayNum' in list(options.keys()) and \
                    options['displayNum']:
                display_num = options['displayNum']
            else:
                display_num = self.virt_pool.alloc_port(self.vm_name, port_type="display")

            vnc_boot_line = '-vnc :%d' % int(display_num)

        self.__add_boot_line(vnc_boot_line)

    def set_vm_vnc(self, **options):
        """
        Set VM display options
        """
        if 'disable' in list(options.keys()):
            vnc_option = [{'disable': 'True'}]
        else:
            if 'displayNum' in list(options.keys()):
                vnc_option = [{'displayNum': options['displayNum']}]
            else:
                # will allocate vnc display later
                vnc_option = [{'disable': 'False'}]

        index = self.find_option_index('vnc')
        if index:
            self.params[index] = {'vnc': vnc_option}
        else:
            self.params.append({'vnc': vnc_option})

    def set_vm_daemon(self, enable='yes'):
        """
        Set VM daemon option.
        """
        index = self.find_option_index('daemon')
        if index:
            self.params[index] = {'daemon': [{'enable': '%s' % enable}]}
        else:
            self.params.append({'daemon': [{'enable': '%s' % enable}]})

    def add_vm_daemon(self, **options):
        """
        enable: 'yes'
            note:
                By default VM will start with the daemonize status.
                Not support starting it on the stdin now.
        """
        if 'daemon' in list(options.keys()) and \
                options['enable'] == 'no':
            pass
        else:
            daemon_boot_line = '-daemonize'
            self.__add_boot_line(daemon_boot_line)

    def add_vm_usercmd(self, **options):
        """
        usercmd: user self defined command line.
                 This command will be add into qemu boot command.
        """
        if 'cmd' in list(options.keys()):
            cmd = options['cmd']
        self.__add_boot_line(cmd)

    def add_vm_crypto(self, **options):
        """
        Add VM crypto options
        """
        separator = ' '

        if 'enable' in list(options.keys()) and options['enable'] == 'yes':
            if 'opt_num' in list(options.keys()):
                opt_num = int(options['opt_num'])
            else:
                opt_num = 1

            for id in range(opt_num):
                cryptodev_id = '%(vm_name)s_crypto%(id)s' % {'vm_name': self.vm_name, 'id': id}
                cryptodev_soch_path = '/tmp/%(vm_name)s_crypto%(id)s.sock' % {'vm_name': self.vm_name, 'id': id}

                crypto_boot_block = '-chardev socket,path=%(SOCK_PATH)s,id=%(ID)s' + separator +\
                                    '-object cryptodev-vhost-user,id=cryptodev%(id)s,chardev=%(ID)s' + separator +\
                                    '-device virtio-crypto-pci,id=crypto%(id)s,cryptodev=cryptodev%(id)s'
                crypto_boot_line = crypto_boot_block % {'SOCK_PATH': cryptodev_soch_path,
                                                        'ID': cryptodev_id,
                                                        'id': id}
                self.__add_boot_line(crypto_boot_line)

    def _check_vm_status(self):
        """
        Check and restart QGA if not ready, wait for network ready
        """
        self.__wait_vm_ready()

        self.__wait_vmnet_ready()

    def _attach_vm(self):
        """
        Attach VM
        Collected information : serial/monitor/qga sock file
                              : hostfwd address
        """
        self.am_attached = True

        if not self._query_pid():
            raise StartVMFailedException("Can't strip process pid!!!")

        cmdline = self.host_session.send_expect('cat /proc/%d/cmdline' % self.pid, '# ')
        qemu_boot_line = cmdline.replace('\x00', ' ')
        self.qemu_boot_line = qemu_boot_line.split(' ', 1)[1]
        self.qemu_emulator = qemu_boot_line.split(' ', 1)[0]

        serial_reg = ".*serial\x00unix:(.*?),"
        telnet_reg = ".*serial\x00telnet::(\d+),"
        monitor_reg = ".*monitor\x00unix:(.*?),"
        hostfwd_reg = ".*hostfwd=tcp:(.*):(\d+)-:"
        migrate_reg = ".*incoming\x00tcp::(\d+)"

        # support both telnet and unix domain socket serial device
        m = re.match(serial_reg, cmdline)
        if not m:
            m1 = re.match(telnet_reg, cmdline)
            if not m1:
                raise StartVMFailedException("No serial sock available!!!")
            else:
                self.serial_port = int(m1.group(1))
                self.control_type = "telnet"
        else:
            self.serial_path = m.group(1)
            self.control_type = "socket"

        m = re.match(monitor_reg, cmdline)
        if not m:
            raise StartVMFailedException("No monitor sock available!!!")
        self.monitor_sock_path = m.group(1)

        m = re.match(hostfwd_reg, cmdline)
        if not m:
            raise StartVMFailedException("No host fwd config available!!!")

        self.net_type = 'hostfwd'
        self.host_port = m.group(2)
        self.hostfwd_addr = m.group(1) + ':' + self.host_port

        # record start time, need call before check_vm_status
        self.start_time = time.time()

        try:
            self.update_status()
        except:
            self.host_logger.error("Can't query vm status!!!")

        if self.vm_status is not ST_PAUSE:
            self._check_vm_status()
        else:
            m = re.match(migrate_reg, cmdline)
            if not m:
                raise StartVMFailedException("No migrate port available!!!")

            self.migrate_port = int(m.group(1))

    def _start_vm(self):
        """
        Start VM.
        """
        self.__alloc_assigned_pcis()

        qemu_boot_line = self.generate_qemu_boot_line()

        self.__send_qemu_cmd(qemu_boot_line, dut_id=self.host_dut.dut_id)

        self.__get_pci_mapping()

        # query status
        self.update_status()

        # sleep few seconds for bios/grub
        time.sleep(10)

        # when vm is waiting for migration, can't ping
        if self.vm_status is not ST_PAUSE:
            self.__wait_vm_ready()

            self.__wait_vmnet_ready()

    # Start VM using the qemu command
    # lock critical action like start qemu
    @parallel_lock(num=4)
    def __send_qemu_cmd(self, qemu_boot_line, dut_id):
        # add more time for qemu start will be slow when system is busy
        ret = self.host_session.send_expect(qemu_boot_line, '# ', verify=True, timeout=30)

        # record start time
        self.start_time = time.time()

        # wait for qemu process ready
        time.sleep(2)
        if type(ret) is int and ret != 0:
            raise StartVMFailedException('Start VM failed!!!')

    def _quick_start_vm(self):
        self.__alloc_assigned_pcis()

        qemu_boot_line = self.generate_qemu_boot_line()

        self.__send_qemu_cmd(qemu_boot_line, dut_id=self.host_dut.dut_id)

        self.__get_pci_mapping()

        # query status
        self.update_status()

        # sleep few seconds for bios and grub
        time.sleep(10)

    def __ping_vm(self):
        logged_in = False
        cur_time = time.time()
        time_diff = cur_time - self.start_time
        try_times = 0
        while (time_diff < self.START_TIMEOUT):
            if self.control_command('ping') == "Success":
                logged_in = True
                break

            # update time consume
            cur_time = time.time()
            time_diff = cur_time - self.start_time

            self.host_logger.warning("Can't login [%s] on [%s], retry %d times!!!" % (self.vm_name, self.host_dut.crb['My IP'], try_times + 1))
            time.sleep(self.OPERATION_TIMEOUT)
            try_times += 1
            continue

        return logged_in

    def __wait_vm_ready(self):
        logged_in = self.__ping_vm()
        if not logged_in:
            if not self.restarted:
                # make sure serial session has been quit
                self.close_control_session(dut_id=self.host_dut.dut_id)
                self.vm_status = ST_NOTSTART
                self._stop_vm()
                self.restarted = True
                self._start_vm()
            else:
                raise StartVMFailedException('Not response in %d seconds!!!' % self.START_TIMEOUT)

    def start_migration(self, remote_ip, remote_port):
        """
        Send migration command to host and check whether start migration
        """
        # send migration command
        migration_port = 'tcp:%(IP)s:%(PORT)s' % {
            'IP': remote_ip, 'PORT': remote_port}

        self.__monitor_session('migrate', '-d', migration_port)
        time.sleep(2)
        out = self.__monitor_session('info', 'migrate')
        if "Migration status: active" in out:
            return True
        else:
            return False

    def wait_migration_done(self):
        """
        Wait for migration done. If not finished after three minutes
        will raise exception.
        """
        # wait for migration done
        count = 30
        while count:
            out = self.__monitor_session('info', 'migrate')
            if "completed" in out:
                self.host_logger.info("%s" % out)
                # after migration done, status is pause
                self.vm_status = ST_PAUSE
                return True

            time.sleep(6)
            count -= 1

        raise StartVMFailedException(
            'Virtual machine can not finished in 180 seconds!!!')

    def generate_qemu_boot_line(self):
        """
        Generate the whole QEMU boot line.
        """
        if self.vcpus_pinned_to_vm:
            vcpus = self.vcpus_pinned_to_vm.replace(' ', ',')
            qemu_boot_line = 'taskset -c %s ' % vcpus + \
                             self.qemu_emulator + ' ' + \
                             self.qemu_boot_line
        else:
            qemu_boot_line = self.qemu_emulator + ' ' + \
                             self.qemu_boot_line

        return qemu_boot_line

    def __get_vmnet_pci(self):
        """
        Get PCI ID of access net interface on VM
        """
        if not getattr(self, 'nic_model', None) is None:
            pci_reg = r'^.*Bus(\s+)(\d+), device(\s+)(\d+), function (\d+)'
            dev_reg = r'^.*Ethernet controller:.*([a-fA-F0-9]{4}:[a-fA-F0-9]{4})'
            if self.nic_model == "e1000":
                dev_id = "8086:100e"
            elif self.nic_model == "i82551":
                dev_id = "8086:1209"
            elif self.nic_model == "virtio":
                dev_id = "1af4:1000"
            out = self.__monitor_session('info', 'pci')
            lines = out.split("\r\n")
            for line in lines:
                m = re.match(pci_reg, line)
                o = re.match(dev_reg, line)
                if m:
                    pci = "%02d:%02d.%d" % (
                        int(m.group(2)), int(m.group(4)), int(m.group(5)))
                if o:
                    if o.group(1) == dev_id:
                        self.net_nic_pci = pci

    def __wait_vmnet_ready(self):
        """
        wait for 120 seconds for vm net ready
        10.0.2.* is the default ip address allocated by qemu
        """
        cur_time = time.time()
        time_diff = cur_time - self.start_time
        try_times = 0
        network_ready = False
        while (time_diff < self.START_TIMEOUT):
            if getattr(self, 'net_nic_pci', None) is None:
                self.__get_vmnet_pci()
            if self.control_command("network") == "Success":
                pos = self.hostfwd_addr.find(':')
                ssh_key = '[' + self.hostfwd_addr[:pos] + ']' + self.hostfwd_addr[pos:]
                os.system('ssh-keygen -R %s' % ssh_key)
                network_ready = True
                break

            # update time consume
            cur_time = time.time()
            time_diff = cur_time - self.start_time

            self.host_logger.warning("[%s] on [%s] network not ready, retry %d times!!!" % (self.vm_name, self.host_dut.crb['My IP'], try_times + 1))
            time.sleep(self.OPERATION_TIMEOUT)
            try_times += 1
            continue

        if network_ready:
            return True
        else:
            raise StartVMFailedException('Virtual machine control net not ready!!!')

    def __alloc_vcpus(self):
        """
        Allocate virtual CPUs for VM.
        """
        req_cpus = self.vcpus_pinned_to_vm.split()
        cpus = self.virt_pool.alloc_cpu(vm=self.vm_name, corelist=req_cpus)

        if len(req_cpus) != len(cpus):
            self.host_logger.warning(
                "VCPUs not enough, required [ %s ], just [ %s ]" %
                                     (req_cpus, cpus))
            raise Exception("No enough required vcpus!!!")

        vcpus_pinned_to_vm = ''
        for cpu in cpus:
            vcpus_pinned_to_vm += ',' + cpu
        vcpus_pinned_to_vm = vcpus_pinned_to_vm.lstrip(',')

        return vcpus_pinned_to_vm

    def __alloc_assigned_pcis(self):
        """
        Record the PCI device info
        Struct: {dev pci: {'is_vf': [True | False],
                            'pf_pci': pci}}
        example:
            {'08:10.0':{'is_vf':True, 'pf_pci': 08:00.0}}
        """
        assigned_pcis_info = {}
        for pci in self.assigned_pcis:
            assigned_pcis_info[pci] = {}
            if self.__is_vf_pci(pci):
                assigned_pcis_info[pci]['is_vf'] = True
                pf_pci = self.__map_vf_to_pf(pci)
                assgined_pcis_info[pci]['pf_pci'] = pf_pci
                if self.virt_pool.alloc_vf_from_pf(vm=self.vm_name,
                                                   pf_pci=pf_pci,
                                                   *[pci]):
                    port = self.__get_vf_port(pci)
                    port.unbind_driver()
                    port.bind_driver('pci-stub')
            else:
                # check that if any VF of specified PF has been
                # used, raise exception
                vf_pci = self.__vf_has_been_assinged(pci, **assinged_pcis_info)
                if vf_pci:
                    raise Exception(
                        "Error: A VF [%s] generated by PF [%s] has " %
                        (vf_pci, pci) +
                        "been assigned to VM, so this PF can not be " +
                        "assigned to VM again!")
                # get the port instance of PF
                port = self.__get_net_device_by_pci(pci)

                if self.virt_pool.alloc_pf(vm=self.vm_name,
                                           *[pci]):
                    port.unbind_driver()

    def __is_vf_pci(self, dev_pci):
        """
        Check if the specified PCI dev is a VF.
        """
        for port_info in self.host_dut.ports_info:
            if 'sriov_vfs_pci' in list(port_info.keys()):
                if dev_pci in port_info['sriov_vfs_pci']:
                    return True
        return False

    def __map_vf_to_pf(self, dev_pci):
        """
        Map the specified VF to PF.
        """
        for port_info in self.host_dut.ports_info:
            if 'sriov_vfs_pci' in list(port_info.keys()):
                if dev_pci in port_info['sriov_vfs_pci']:
                    return port_info['pci']
        return None

    def __get_vf_port(self, dev_pci):
        """
        Get the NetDevice instance of specified VF.
        """
        for port_info in self.host_dut.ports_info:
            if 'vfs_port' in list(port_info.keys()):
                for port in port_info['vfs_port']:
                    if dev_pci == port.pci:
                        return port
        return None

    def __vf_has_been_assigned(self, pf_pci, **assigned_pcis_info):
        """
        Check if the specified VF has been used.
        """
        for pci in list(assigned_pcis_info.keys()):
            if assigned_pcis_info[pci]['is_vf'] and \
                    assigned_pcis_info[pci]['pf_pci'] == pf_pci:
                return pci
        return False

    def __get_net_device_by_pci(self, net_device_pci):
        """
        Get NetDevice instance by the specified PCI bus number.
        """
        port_info = self.host_dut.get_port_info(net_device_pci)
        return port_info['port']

    def get_vm_ip(self):
        """
        Get VM IP.
        """
        get_vm_ip = getattr(self, "get_vm_ip_%s" % self.net_type)
        return get_vm_ip()

    def get_vm_ip_hostfwd(self):
        """
        Get IP which VM is connected by hostfwd.
        """
        return self.hostfwd_addr

    def get_vm_ip_bridge(self):
        """
        Get IP which VM is connected by bridge.
        """
        out = self.control_command('ping', '60')
        if not out:
            time.sleep(10)
            out = self.control_command('ifconfig')
            ips = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', out)

            if '127.0.0.1' in ips:
                ips.remove('127.0.0.1')

            num = 3
            for ip in ips:
                out = self.host_session.send_expect(
                    'ping -c %d %s' % (num, ip), '# ')
                if '0% packet loss' in out:
                    return ip
        return ''

    def __get_pci_mapping(self):
        devices = self.__strip_guest_pci()
        for hostpci in self.pt_devices:
            index = self.pt_devices.index(hostpci)
            pt_id = 'pt_%d' % index
            pci_map = {}
            for device in devices:
                if device['id'] == pt_id:
                    pci_map['hostpci'] = hostpci
                    pci_map['guestpci'] = device['pci']
                    self.pci_maps.append(pci_map)

    def get_pci_mappings(self):
        """
        Return guest and host pci devices mapping structure
        """
        return self.pci_maps

    def __monitor_session(self, command, *args):
        """
        Connect the qemu monitor session, send command and return output message.
        """
        if not self.monitor_sock_path:
            self.host_logger.info(
                "No monitor between on host [ %s ] for guest [ %s ]" %
                (self.host_dut.NAME, self.vm_name))
            return None

        self.host_session.send_expect(
            'nc -U %s' % self.monitor_sock_path, '(qemu)')

        cmd = command
        for arg in args:
            cmd += ' ' + str(arg)

        # after quit command, qemu will exit
        if 'quit' in cmd:
            self.host_session.send_command('%s' % cmd)
            out = self.host_session.send_expect(' ', '#')
        else:
            out = self.host_session.send_expect('%s' % cmd, '(qemu)', 30)
        self.host_session.send_expect('^C', "# ")
        return out

    def update_status(self):
        """
        Query and update VM status
        """
        out = self.__monitor_session('info', 'status')
        self.host_logger.warning("Virtual machine status: %s" % out)

        if 'paused' in out:
            self.vm_status = ST_PAUSE
        elif 'running' in out:
            self.vm_status = ST_RUNNING
        else:
            self.vm_status = ST_UNKNOWN

        info = self.host_session.send_expect('cat %s' % self.__pid_file, "# ")
        try:
            pid = int(info.split()[0])
            # save pid into dut structure
            self.host_dut.virt_pids.append(pid)
        except:
            self.host_logger.info("Failed to capture pid!!!")

    def _query_pid(self):
        info = self.host_session.send_expect('cat %s' % self.__pid_file, "# ")
        try:
            # sometimes saw to lines in pid file
            pid = int(info.splitlines()[0])
            # save pid into dut structure
            self.pid = pid
            return True
        except:
            return False

    def __strip_guest_pci(self):
        """
        Strip all pci-passthrough device information, based on qemu monitor
        """
        pci_reg = r'^.*Bus(\s+)(\d+), device(\s+)(\d+), function (\d+)'
        id_reg = r'^.*id \"(.*)\"'

        pcis = []
        out = self.__monitor_session('info', 'pci')

        if out is None:
            return pcis

        lines = out.split("\r\n")

        for line in lines:
            m = re.match(pci_reg, line)
            n = re.match(id_reg, line)
            if m:
                pci = "%02d:%02d.%d" % (
                    int(m.group(2)), int(m.group(4)), int(m.group(5)))
            if n:
                dev_id = n.group(1)
                if dev_id != '':
                    pt_dev = {}
                    pt_dev['pci'] = pci
                    pt_dev['id'] = dev_id
                    pcis.append(pt_dev)

        return pcis

    def __strip_guest_core(self):
        """
        Strip all lcore-thread binding information
        Return array will be [thread0, thread1, ...]
        """
        cores = []
        # CPU #0: pc=0xffffffff8104c416 (halted) thread_id=40677
        core_reg = r'^.*CPU #(\d+): (.*) thread_id=(\d+)'
        out = self.__monitor_session('info', 'cpus')

        if out is None:
            return cores

        lines = out.split("\r\n")
        for line in lines:
            m = re.match(core_reg, line)
            if m:
                cores.append(int(m.group(3)))

        return cores

    def handle_control_session(func):
        """
        Wrapper function to handle serial port, must return serial to host session
        """
        def _handle_control_session(self, command):
            # just raise error if connect failed, for func can't all any more
            try:
                if self.control_type == 'socket':
                    assert (self.connect_serial_port(name=self.vm_name)), "Can't connect to serial socket"
                elif self.control_type == 'telnet':
                    assert (self.connect_telnet_port(name=self.vm_name)), "Can't connect to serial port"
                else:
                    assert (self.connect_qga_port(name=self.vm_name)), "Can't connect to qga port"
            except:
                return 'Failed'

            try:
                out = func(self, command)
                self.quit_control_session()
                return out
            except Exception as e:
                print(RED("Exception happened on [%s] serial with cmd [%s]" % (self.vm_name, command)))
                print(RED(e))
                self.close_control_session(dut_id=self.host_dut.dut_id)
                return 'Failed'

        return _handle_control_session

    def quit_control_session(self):
        """
        Quit from serial session gracefully
        """
        if self.control_type == 'socket':
            self.control_session.send_expect("^C", "# ")
        elif self.control_type == 'telnet':
            self.control_session.send_command("^]")
            self.control_session.send_command("quit")
        # nothing need to do for qga session
        self.control_session = None

    @parallel_lock()
    def close_control_session(self, dut_id):
        """
        Force kill serial connection from DUT when exception happened
        """
        # return control_session to host_session
        if self.control_type == 'socket':
            scan_cmd = "ps -e -o pid,cmd  |grep 'socat %s STDIO' |grep -v grep" % self.serial_path
            out = self.host_dut.send_expect(scan_cmd, "#")
            proc_info = out.strip().split()
            try:
                pid = int(proc_info[0])
                self.host_dut.send_expect('kill %d' % pid, "#")
            except:
                pass
            self.host_dut.send_expect("", "# ")
        elif self.control_type == 'telnet':
            scan_cmd = "lsof -i:%d | grep telnet | awk '{print $2}'" % self.serial_port
            proc_info = self.host_dut.send_expect(scan_cmd, "#")
            try:
                pid = int(proc_info)
                self.host_dut.send_expect('kill %d' % pid, "#")
            except:
                pass
        elif self.control_type == 'qga':
            scan_cmd = "ps -e -o pid,cmd  |grep 'address=%s' |grep -v grep" % self.qga_socket_path
            out = self.host_dut.send_expect(scan_cmd, "#")
            proc_info = out.strip().split()
            try:
                pid = int(proc_info[0])
                self.host_dut.send_expect('kill %d' % pid, "#")
            except:
                pass

        self.control_session = None
        return

    @handle_control_session
    def control_command(self, command):
        """
        Use the serial port to control VM.
        Note:
            :command: there are these commands as below:
                    ping, network, powerdown
            :args: give different args by the different commands.
        """

        if command == "ping":
            if self.control_type == "qga":
                return "Success"
            else:
                # disable stty input characters for send_expect function
                self.control_session.send_expect("stty -echo", "#", timeout=self.OPERATION_TIMEOUT)
                return "Success"
        elif command == "network":
            if self.control_type == "qga":
                # wait few seconds for network ready
                time.sleep(5)
                out = self.control_session.send_expect(self.qga_cmd_head + "ifconfig" , "#", timeout=self.OPERATION_TIMEOUT)
            else:
                pci = "00:1f.0"
                if not getattr(self, 'net_nic_pci', None) is None:
                    pci = self.net_nic_pci
                    ## If interface is vritio model, net file will be under virtio* directory
                    if self.nic_model == "virtio":
                        pci += "/virtio*/"

                intf = self.control_session.send_expect("ls -1 /sys/bus/pci/devices/0000:%s/net" %pci, "#", timeout=self.OPERATION_TIMEOUT)
                out = self.control_session.send_expect("ifconfig %s" % intf, "#", timeout=self.OPERATION_TIMEOUT)
                if "10.0.2" not in out:
                    self.control_session.send_expect("dhclient %s -timeout 10" % intf, "#", timeout=30)
                else:
                    return "Success"

                out = self.control_session.send_expect("ifconfig", "#", timeout=self.OPERATION_TIMEOUT)

            if "10.0.2" not in out:
                return "Failed"
            else:
                return "Success"
        elif command == "powerdown":
            if self.control_type == "qga":
                self.control_session.send_expect(self.qga_cmd_head + "powerdown", "#", timeout=self.OPERATION_TIMEOUT)
            else:
                self.control_session.send_command("init 0")

            if self.control_type == "socket":
                self.control_session.send_expect("^C", "# ")
            elif self.control_type == "telnet":
                self.control_session.send_command("^]")
                self.control_session.send_command("quit")

            time.sleep(10)
            self.kill_alive()
            return "Success"
        else:
            if self.control_type == "qga":
                self.host_logger.warning("QGA not support [%s] command" % command)
                out = "Failed"
            else:
                out = self.control_session.send_command(command)
            return out

    def _stop_vm(self):
        """
        Stop VM.
        """
        if self.vm_status is ST_RUNNING:
            self.control_command('powerdown')
        else:
            self.__monitor_session('quit')
        time.sleep(5)
        # remove temporary file
        self.host_session.send_expect("rm -f %s" % self.__pid_file, "#")

    def pin_threads(self, lcores):
        """
        Pin thread to assigned cores
        """
        thread_reg = r'CPU #(\d+): .* thread_id=(\d+)'
        output = self.__monitor_session('info', 'cpus')
        thread_cores = re.findall(thread_reg, output)
        cores_map = list(zip(thread_cores, lcores))
        for thread_info, core_id in cores_map:
            cpu_id, thread_id = thread_info
            self.host_session.send_expect("taskset -pc %d %s" % (core_id, thread_id), "#")
