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
import sys
import traceback
import threading
from random import randint


import utils
import exception
from dut import Dut
from config import VirtConf
from config import VIRTCONF
from logger import getLogger
from settings import CONFIG_ROOT_PATH
from virt_dut import VirtDut

ST_NOTSTART = "NOTSTART"
ST_PAUSE = "PAUSE"
ST_RUNNING = "RUNNING"
ST_UNKNOWN = "UNKNOWN"
VM_IMG_LIST = []
mutex_vm_list = threading.Lock()

class VirtBase(object):
    """
    Basic module for customer special virtual type. This module implement
    functions configured and composed in the VM boot command. With these
    function, we can get and set the VM boot command, and instantiate the VM.
    """

    def __init__(self, dut, vm_name, suite_name):
        """
        Initialize the VirtBase.
        dut: the instance of Dut
        vm_name: the name of VM which you have configured in the configure
        suite_name: the name of test suite
        """
        self.host_dut = dut
        self.vm_name = vm_name
        self.suite = suite_name
        # indicate whether the current vm is migration vm
        self.migration_vm = False

        # create self used host session, need close it later
        self.host_session = self.host_dut.new_session(self.vm_name)

        self.host_logger = self.host_dut.logger
        # base_dir existed for host dut has prepared it
        self.host_session.send_expect("cd %s" % self.host_dut.base_dir, "# ")

        # init the host resource pool for VM
        self.virt_pool = self.host_dut.virt_pool

        if not self.has_virtual_ability():
            if not self.enable_virtual_ability():
                raise Exception(
                    "Dut [ %s ] cannot have the virtual ability!!!")

        self.virt_type = self.get_virt_type()

        self.params = []
        self.local_conf = []

        # default call back function is None
        self.callback = None

        # vm status is running by default, only be changed in internal module
        self.vm_status = ST_RUNNING

        # by default no special kernel module is required
        self.def_driver = ''
        self.driver_mode = ''

    def get_virt_type(self):
        """
        Get the virtual type, such as KVM, XEN or LIBVIRT.
        """
        NotImplemented

    def has_virtual_ability(self):
        """
        Check if the host have the ability of virtualization.
        """
        NotImplemented

    def enable_virtual_ability(self):
        """
        Enable the virtual ability on the DUT.
        """
        NotImplemented

    def load_global_config(self):
        """
        Load global configure in the path DTS_ROOT_PATH/conf.
        """
        conf = VirtConf(VIRTCONF)
        conf.load_virt_config(self.virt_type)
        global_conf = conf.get_virt_config()
        for param in global_conf:
            for key in list(param.keys()):
                if self.find_option_index(key) is None:
                    self.__save_local_config(key, param[key])

    def set_local_config(self, local_conf):
        """
        Configure VM configuration from user input
        """
        self.local_conf = local_conf

    def load_local_config(self, suite_name):
        """
        Load local configure in the path DTS_ROOT_PATH/conf.
        """
        # load local configuration by suite and vm name
        try:
            conf = VirtConf(CONFIG_ROOT_PATH + os.sep + suite_name + '.cfg')
            conf.load_virt_config(self.vm_name)
            self.local_conf = conf.get_virt_config()
        except:
            # when met exception in load VM config
            # just leave local conf untouched
            pass

        # replace global configurations with local configurations
        for param in self.local_conf:
            if 'virt_type' in list(param.keys()):
                # param 'virt_type' is for virt_base only
                continue
            # save local configurations
            for key in list(param.keys()):
                self.__save_local_config(key, param[key])

    def __save_local_config(self, key, value):
        """
        Save the local config into the global dict self.param.
        """
        for param in self.params:
            if key in list(param.keys()):
                param[key] = value
                return

        self.params.append({key: value})

    def compose_boot_param(self):
        """
        Compose all boot param for starting the VM.
        """
        for param in self.params:
            key = list(param.keys())[0]
            value = param[key]
            try:
                param_func = getattr(self, 'add_vm_' + key)
                if callable(param_func):
                    if type(value) is list:
                        for option in value:
                            param_func(**option)
                else:
                    print(utils.RED("Virt %s function not callable!!!" % key))
            except AttributeError:
                    self.host_logger.error(traceback.print_exception(*sys.exc_info()))
                    print(utils.RED("Virt %s function not implemented!!!" % key))
            except Exception:
                self.host_logger.error(traceback.print_exception(*sys.exc_info()))
                raise exception.VirtConfigParamException(key)

    def add_vm_def_driver(self, **options):
        """
        Set default driver which may required when setup VM
        """
        if 'driver_name' in list(options.keys()):
            self.def_driver = options['driver_name']
        if 'driver_mode' in list(options.keys()):
            self.driver_mode = options['driver_mode']

    def find_option_index(self, option):
        """
        Find the boot option in the params which is generated from
        the global and local configures, and this function will
        return the index by which option can be indexed in the
        param list.
        """
        index = 0
        for param in self.params:
            key = list(param.keys())[0]
            if key.strip() == option.strip():
                return index
            index += 1

        return None

    def generate_unique_mac(self):
        """
        Generate a unique MAC based on the DUT.
        """
        mac_head = '00:00:00:'
        mac_tail = ':'.join(
            ['%02x' % x for x in map(lambda x:randint(0, 255), list(range(3)))])
        return mac_head + mac_tail

    def get_vm_ip(self):
        """
        Get the VM IP.
        """
        NotImplemented

    def get_pci_mappings(self):
        """
        Get host and VM pass-through device mapping
        """
        NotImplemented

    def isalive(self):
        """
        Check whether VM existed.
        """
        vm_status = self.host_session.send_expect(
            "ps aux | grep qemu | grep 'name %s '| grep -v grep"
            % self.vm_name, "# ")

        if self.vm_name in vm_status:
            return True
        else:
            return False

    def load_config(self):
        """
        Load configurations for VM
        """
        # load global and suite configuration file
        self.load_global_config()
        self.load_local_config(self.suite)

    def attach(self):
        # load configuration
        self.load_config()

        # change login user/password
        index = self.find_option_index("login")
        if index:
            value = self.params[index]["login"]
            for option in value:
                self.add_vm_login(**option)

        # attach real vm
        self._attach_vm()
        return None

    def start(self, load_config=True, set_target=True, cpu_topo='', bind_dev=True):
        """
        Start VM and instantiate the VM with VirtDut.
        """
        try:
            if load_config is True:
                self.load_config()
            # compose boot command for different hypervisors
            self.compose_boot_param()

            # start virtual machine
            self._start_vm()

            if self.vm_status is ST_RUNNING:
                # connect vm dut and init running environment
                vm_dut = self.instantiate_vm_dut(set_target, cpu_topo, bind_dev=bind_dev, autodetect_topo=True)
            else:
                vm_dut = None

        except Exception as vm_except:
            if self.handle_exception(vm_except):
                print(utils.RED("Handled exception " + str(type(vm_except))))
            else:
                print(utils.RED("Unhandled exception " + str(type(vm_except))))

            if callable(self.callback):
                self.callback()

            return None
        return vm_dut

    def quick_start(self, load_config=True, set_target=True, cpu_topo=''):
        """
        Only Start VM and not do anything else, will be helpful in multiple VMs
        """
        try:
            if load_config is True:
                self.load_config()
            # compose boot command for different hypervisors
            self.compose_boot_param()

            # start virtual machine
            self._quick_start_vm()

        except Exception as vm_except:
            if self.handle_exception(vm_except):
                print(utils.RED("Handled exception " + str(type(vm_except))))
            else:
                print(utils.RED("Unhandled exception " + str(type(vm_except))))

            if callable(self.callback):
                self.callback()

    def migrated_start(self, set_target=True, cpu_topo=''):
        """
        Instantiate the VM after migration done
        There's no need to load param and start VM because VM has been started
        """
        try:
            if self.vm_status is ST_PAUSE:
                # flag current vm is migration vm
                self.migration_vm = True
                # connect backup vm dut and it just inherited from host
                vm_dut = self.instantiate_vm_dut(set_target, cpu_topo, bind_dev=False, autodetect_topo=False)
        except Exception as vm_except:
            if self.handle_exception(vm_except):
                print(utils.RED("Handled exception " + str(type(vm_except))))
            else:
                print(utils.RED("Unhandled exception " + str(type(vm_except))))

            return None

        return vm_dut

    def handle_exception(self, vm_except):
        # show exception back trace
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback,
                                  limit=2, file=sys.stdout)
        if type(vm_except) is exception.ConfigParseException:
            # nothing to handle just return True
            return True
        elif type(vm_except) is exception.VirtConfigParseException:
            # nothing to handle just return True
            return True
        elif type(vm_except) is exception.VirtConfigParamException:
            # nothing to handle just return True
            return True
        elif type(vm_except) is exception.StartVMFailedException:
            # start vm failure
            return True
        elif type(vm_except) is exception.VirtDutConnectException:
            # need stop vm
            self._stop_vm()
            return True
        elif type(vm_except) is exception.VirtDutInitException:
            # need close session
            vm_except.vm_dut.close()
            # need stop vm
            self.stop()
            return True
        else:
            return False

    def _start_vm(self):
        """
        Start VM.
        """
        NotImplemented

    def _stop_vm(self):
        """
        Stop VM.
        """
        NotImplemented

    def get_vm_img(self):
        """
        get current vm img name from params
        get format like: 10.67.110.11:TestVhostMultiQueueQemu:/home/img/Ub1604.img
        """
        param_len = len(self.params)
        for i in range(param_len):
            if 'disk' in list(self.params[i].keys()):
                value = self.params[i]['disk'][0]
                if 'file' in list(value.keys()):
                    host_ip = self.host_dut.get_ip_address()
                    return host_ip + ':' + self.host_dut.test_classname + ':' + value['file']
        return None

    def instantiate_vm_dut(self, set_target=True, cpu_topo='', bind_dev=True, autodetect_topo=True):
        """
        Instantiate the Dut class for VM.
        """
        crb = self.host_dut.crb.copy()
        crb['bypass core0'] = False
        vm_ip = self.get_vm_ip()
        crb['IP'] = vm_ip
        crb['My IP'] = vm_ip
        username, password = self.get_vm_login()
        crb['user'] = username
        crb['pass'] = password

        serializer = self.host_dut.serializer

        try:
            vm_dut = VirtDut(
                self,
                crb,
                serializer,
                self.virt_type,
                self.vm_name,
                self.suite,
                cpu_topo,
                dut_id=self.host_dut.dut_id)
        except Exception as vm_except:
            self.handle_exception(vm_except)
            raise exception.VirtDutConnectException
            return None

        vm_dut.nic_type = 'any'
        vm_dut.tester = self.host_dut.tester
        vm_dut.host_dut = self.host_dut
        vm_dut.host_session = self.host_session
        vm_dut.init_log()
        vm_dut.migration_vm = self.migration_vm

        read_cache = False
        skip_setup = self.host_dut.skip_setup
        vm_img = self.get_vm_img()
        # if current vm is migration vm, skip compile dpdk
        # if VM_IMG_list include the vm_img, it means the vm have complie the dpdk ok, skip it
        if self.migration_vm or vm_img in VM_IMG_LIST:
            skip_setup = True
        base_dir = self.host_dut.base_dir
        vm_dut.set_speedup_options(read_cache, skip_setup)

        # package and patch should be set before prerequisites
        vm_dut.set_package(self.host_dut.package, self.host_dut.patches)

        # base_dir should be set before prerequisites
        vm_dut.set_directory(base_dir)

        try:
            # setting up dpdk in vm, must call at last
            vm_dut.target = self.host_dut.target
            vm_dut.prerequisites(self.host_dut.package, self.host_dut.patches, autodetect_topo)
            if set_target:
                target = self.host_dut.target
                vm_dut.set_target(target, bind_dev, self.def_driver, self.driver_mode)
        except:
            raise exception.VirtDutInitException(vm_dut)
            return None

        # after prerequisites and set_target, the dpdk compile is ok, add this vm img to list
        if vm_img not in VM_IMG_LIST:
            mutex_vm_list.acquire()
            VM_IMG_LIST.append(vm_img)
            mutex_vm_list.release()

        self.vm_dut = vm_dut
        return vm_dut

    def stop(self):
        """
        Stop the VM.
        """
        self._stop_vm()
        self.quit()

        self.virt_pool.free_all_resource(self.vm_name)

    def quit(self):
        """
        Just quit connection to the VM
        """
        if getattr(self, 'host_session', None):
            self.host_session.close()
            self.host_session = None

        # vm_dut may not init in migration case
        if getattr(self, 'vm_dut', None):
            if self.vm_status is ST_RUNNING:
                self.vm_dut.close()
            else:
                # when vm is not running, not close session forcely
                self.vm_dut.close(force=True)

            self.vm_dut.logger.logger_exit()
            self.vm_dut = None

    def register_exit_callback(self, callback):
        """
        Call register exit call back function
        """
        self.callback = callback
