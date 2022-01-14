# BSD LICENSE
#
# Copyright(c) 2010-2021 Intel Corporation. All rights reserved.
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

"""
Generic port and crbs configuration file load function
"""
import argparse  # parse arguments module
import configparser  # config parse module
import os
import re

from .exception import (
    ConfigParseException,
    PortConfigParseException,
    VirtConfigParseException,
)
from .settings import (
    CONFIG_ROOT_PATH,
    DTS_CFG_FOLDER,
    PKTGEN,
    PKTGEN_DPDK,
    PKTGEN_IXIA,
    PKTGEN_IXIA_NETWORK,
    PKTGEN_TREX,
    SUITE_SECTION_NAME,
    load_global_setting,
)

PORTCONF = "%s/ports.cfg" % CONFIG_ROOT_PATH
CRBCONF = "%s/crbs.cfg" % CONFIG_ROOT_PATH
VIRTCONF = "%s/virt_global.cfg" % CONFIG_ROOT_PATH
IXIACONF = "%s/ixia.cfg" % CONFIG_ROOT_PATH
PKTGENCONF = "%s/pktgen.cfg" % CONFIG_ROOT_PATH
SUITECONF_SAMPLE = "%s/suite_sample.cfg" % CONFIG_ROOT_PATH
GLOBALCONF = "%s/global_suite.cfg" % CONFIG_ROOT_PATH
APPNAMECONF = "%s/app_name.cfg" % CONFIG_ROOT_PATH


class UserConf():

    def __init__(self, config):
        self.conf = configparser.SafeConfigParser()
        load_files = self.conf.read(config)
        if load_files == []:
            self.conf = None
            raise ConfigParseException(config)

    def get_sections(self):
        if self.conf is None:
            return []

        return self.conf.sections()

    def load_section(self, section):
        if self.conf is None:
            return None

        items = None
        for conf_sect in self.conf.sections():
            if conf_sect == section:
                items = self.conf.items(section)

        return items

    def load_config(self, item):
        confs = [conf.strip() for conf in item.split(';')]
        if '' in confs:
            confs.remove('')
        return confs

    def load_param(self, conf):
        paramDict = dict()

        for param in conf.split(','):
            (key, _, value) = param.partition('=')
            paramDict[key] = value
        return paramDict


class GlobalConf(UserConf):
    def __init__(self):
        self.global_cfg = {}
        try:
            self.global_conf = UserConf(GLOBALCONF)
        except ConfigParseException:
            self.global_conf = None

        # load global configuration
        self.global_cfg = self.load_global_config()

    def load_global_config(self, section_name='global'):
        global_cfg = self.global_cfg.copy()
        try:
            section_confs = self.global_conf.load_section(section_name)
        except:
            print("FAILED FIND SECTION[%s] CONFIG!!!" % section_name)
            return global_cfg

        if section_confs is None:
            return global_cfg

        global_cfg = dict(section_confs)

        return global_cfg


class SuiteConf(UserConf):
    def __init__(self, suite_name=""):
        self.suite_cfg = GlobalConf().load_global_config()
        self.config_file = CONFIG_ROOT_PATH + os.sep + suite_name + ".cfg"
        try:
            self.suite_conf = UserConf(self.config_file)
        except ConfigParseException:
            self.suite_conf = None

        # load default suite configuration
        self.suite_cfg = self.load_case_config(SUITE_SECTION_NAME)

    def load_case_config(self, case_name=""):
        case_cfg = self.suite_cfg.copy()
        if self.suite_conf is None:
            return case_cfg

        try:
            case_confs = self.suite_conf.load_section(case_name)
        except:
            print("FAILED FIND CASE[%s] CONFIG!!!" % case_name)
            return case_cfg

        if case_confs is None:
            return case_cfg

        conf = dict(case_confs)
        for key, data_string in list(conf.items()):
            try:
                case_cfg[key] = eval(data_string)
            except NameError:  # happens when data_string is actually a string, not an int, bool or dict
                case_cfg[key] = data_string

        return case_cfg

    def update_case_config(self, case_name=""):
        """
        update section (case_name) of the configure file
        """
        update_suite_cfg_obj = UserConf(self.config_file)
        update_suite_cfg = update_suite_cfg_obj.load_section(case_name)
        for key in update_suite_cfg_obj.conf.options(case_name):
            update_suite_cfg_obj.conf.set(
                case_name, key, str(self.suite_cfg[key]))
        update_suite_cfg_obj.conf.write(open(self.config_file, 'w'))


class VirtConf(UserConf):

    def __init__(self, virt_conf=VIRTCONF):
        self.config_file = virt_conf
        self.virt_cfg = {}
        try:
            self.virt_conf = UserConf(self.config_file)
        except ConfigParseException:
            self.virt_conf = None
            raise VirtConfigParseException

    def load_virt_config(self, name):
        self.virt_cfgs = []

        try:
            virt_confs = self.virt_conf.load_section(name)
        except:
            print("FAILED FIND SECTION %s!!!" % name)
            return

        for virt_conf in virt_confs:
            virt_cfg = {}
            virt_params = []
            key, config = virt_conf
            confs = self.virt_conf.load_config(config)
            for config in confs:
                virt_params.append(self.load_virt_param(config))
            virt_cfg[key] = virt_params
            self.virt_cfgs.append(virt_cfg)

    def get_virt_config(self):
        return self.virt_cfgs

    def load_virt_param(self, config):
        cfg_params = self.virt_conf.load_param(config)
        return cfg_params


class PortConf(UserConf):

    def __init__(self, port_conf=PORTCONF):
        self.config_file = port_conf
        self.ports_cfg = {}
        self.pci_regex = "([\da-f]{4}:[\da-f]{2}:[\da-f]{2}.\d{1})$"
        try:
            self.port_conf = UserConf(self.config_file)
        except ConfigParseException:
            self.port_conf = None
            raise PortConfigParseException

    def load_ports_config(self, crbIP):
        self.ports_cfg = {}
        if self.port_conf is None:
            return

        ports = self.port_conf.load_section(crbIP)
        if ports is None:
            return
        key, config = ports[0]
        confs = self.port_conf.load_config(config)

        for config in confs:
            port_param = self.port_conf.load_param(config)

            # port config for vm in virtualization scenario
            if 'dev_idx' in port_param:
                keys = list(port_param.keys())
                keys.remove('dev_idx')
                self.ports_cfg[port_param['dev_idx']] = {
                    key: port_param[key] for key in keys}
                continue

            # check pci BDF validity
            if 'pci' not in port_param:
                print("NOT FOUND CONFIG FOR NO PCI ADDRESS!!!")
                continue
            m = re.match(self.pci_regex, port_param['pci'])
            if m is None:
                print("INVALID CONFIG FOR NO PCI ADDRESS!!!")
                continue

            keys = list(port_param.keys())
            keys.remove('pci')
            self.ports_cfg[port_param['pci']] = {
                key: port_param[key] for key in keys}
            if 'numa' in self.ports_cfg[port_param['pci']]:
                numa_str = self.ports_cfg[port_param['pci']]['numa']
                self.ports_cfg[port_param['pci']]['numa'] = int(numa_str)

    def get_ports_config(self):
        return self.ports_cfg

    def check_port_available(self, pci_addr):
        if pci_addr in list(self.ports_cfg.keys()):
            return True
        else:
            return False


class CrbsConf(UserConf):
    DEF_CRB = {'IP': '', 'board': 'default', 'user': '',
               'pass': '', 'tester IP': '', 'tester pass': '',
               'memory channels': 4,
               PKTGEN: None,
               'bypass core0': True, 'dut_cores': '',
               'snapshot_load_side': 'tester'}

    def __init__(self, crbs_conf=CRBCONF):
        self.config_file = crbs_conf
        self.crbs_cfg = []
        try:
            self.crbs_conf = UserConf(self.config_file)
        except ConfigParseException:
            self.crbs_conf = None
            raise ConfigParseException

    def load_crbs_config(self):
        sections = self.crbs_conf.get_sections()
        if not sections:
            return self.crbs_cfg

        for name in sections:
            crb = self.DEF_CRB.copy()
            crb['section'] = name
            crb_confs = self.crbs_conf.load_section(name)
            if not crb_confs:
                continue

            # convert file configuration to dts crbs
            for conf in crb_confs:
                key, value = conf
                if key == 'dut_ip':
                    crb['IP'] = value
                elif key == 'dut_user':
                    crb['user'] = value
                elif key == 'dut_passwd':
                    crb['pass'] = value
                elif key == 'os':
                    crb['OS'] = value
                elif key == 'tester_ip':
                    crb['tester IP'] = value
                elif key == 'tester_passwd':
                    crb['tester pass'] = value
                elif key == 'pktgen_group':
                    crb[PKTGEN] = value.lower()
                elif key == 'channels':
                    crb['memory channels'] = int(value)
                elif key == 'bypass_core0':
                    if value == 'True':
                        crb['bypass core0'] = True
                    else:
                        crb['bypass core0'] = False
                elif key == 'board':
                    crb['board'] = value
                elif key == 'dut_arch':
                    crb['dut arch'] = value
                elif key == 'dut_cores':
                    crb['dut_cores'] = value
                elif key == 'snapshot_load_side':
                    crb['snapshot_load_side'] = value.lower()

            self.crbs_cfg.append(crb)
        return self.crbs_cfg


class PktgenConf(UserConf):

    def __init__(self, pktgen_type='ixia', pktgen_conf=PKTGENCONF):
        self.config_file = pktgen_conf
        self.pktgen_type = pktgen_type.lower()
        self.pktgen_cfg = {}
        try:
            self.pktgen_conf = UserConf(self.config_file)
        except ConfigParseException:
            self.pktgen_conf = None
            raise ConfigParseException

    def load_pktgen_ixia_config(self, section):
        port_reg = r'card=(\d+),port=(\d+)'
        pktgen_confs = self.pktgen_conf.load_section(section)
        if not pktgen_confs:
            return
        # convert file configuration to dts ixiacfg
        ixia_group = {}
        for conf in pktgen_confs:
            key, value = conf
            if key == 'ixia_version':
                ixia_group['Version'] = value
            elif key == 'ixia_ip':
                ixia_group['IP'] = value
            elif key == 'ixia_ports':
                ports = self.pktgen_conf.load_config(value)
                ixia_ports = []
                for port in ports:
                    m = re.match(port_reg, port)
                    if m:
                        ixia_port = {}
                        ixia_port["card"] = int(m.group(1))
                        ixia_port["port"] = int(m.group(2))
                        ixia_ports.append(ixia_port)
                ixia_group['Ports'] = ixia_ports
            elif key == 'ixia_enable_rsfec':
                ixia_group['enable_rsfec'] = value
            else:
                ixia_group[key] = value

        if 'Version' not in ixia_group:
            print('ixia configuration file request ixia_version option!!!')
            return
        if 'IP' not in ixia_group:
            print('ixia configuration file request ixia_ip option!!!')
            return
        if 'Ports' not in ixia_group:
            print('ixia configuration file request ixia_ports option!!!')
            return

        self.pktgen_cfg[section.lower()] = ixia_group

    def load_pktgen_config(self):
        sections = self.pktgen_conf.get_sections()
        if not sections:
            return self.pktgen_cfg

        for section in sections:
            if self.pktgen_type == PKTGEN_DPDK and section.lower() == PKTGEN_DPDK:
                pktgen_confs = self.pktgen_conf.load_section(section)
                if not pktgen_confs:
                    continue

                # covert file configuration to dts pktgen cfg
                for conf in pktgen_confs:
                    key, value = conf
                    self.pktgen_cfg[key] = value
            elif self.pktgen_type == PKTGEN_TREX and section.lower() == PKTGEN_TREX:
                pktgen_confs = self.pktgen_conf.load_section(section)
                if not pktgen_confs:
                    continue

                # covert file configuration to dts pktgen cfg
                for conf in pktgen_confs:
                    key, value = conf
                    self.pktgen_cfg[key] = value
            elif (self.pktgen_type == PKTGEN_IXIA and section.lower() == PKTGEN_IXIA) or \
                 (self.pktgen_type == PKTGEN_IXIA_NETWORK and section.lower() == PKTGEN_IXIA_NETWORK):
                # covert file configuration to dts pktgen cfg
                self.load_pktgen_ixia_config(section)

        return self.pktgen_cfg

class AppNameConf(UserConf):
    def __init__(self, app_name_conf=APPNAMECONF):
        self.config_file = app_name_conf
        self.app_name_cfg = {}
        try:
            self.app_name_conf = UserConf(self.config_file)
        except ConfigParseException:
            self.app_name_conf = None
            raise ConfigParseException

    def load_app_name_conf(self):
        sections = self.app_name_conf.get_sections()
        if not sections:
            return self.app_name_cfg

        for build_type in sections:
            cur_name_cfg = self.app_name_conf.load_section(build_type)
            if not cur_name_cfg:
                continue

            name_cfg = {}
            for cfg in cur_name_cfg:
                key, value = cfg
                name_cfg[key] = value

            self.app_name_cfg[build_type.lower()]=name_cfg

        return self.app_name_cfg

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Load DTS configuration files")
    parser.add_argument("-p", "--portconf", default=PORTCONF)
    parser.add_argument("-c", "--crbconf", default=CRBCONF)
    parser.add_argument("-v", "--virtconf", default=VIRTCONF)
    parser.add_argument("-i", "--ixiaconf", default=IXIACONF)
    args = parser.parse_args()

    # not existed configuration file
    try:
        VirtConf('/tmp/not-existed.cfg')
    except VirtConfigParseException:
        print("Capture config parse failure")

    # example for basic use configuration file
    conf = UserConf(PORTCONF)
    for section in conf.get_sections():
        items = conf.load_section(section)
        key, value = items[0]
        confs = conf.load_config(value)
        for config in confs:
            conf.load_param(config)

    # example for port configuration file
    portconf = PortConf(PORTCONF)
    portconf.load_ports_config('DUT IP')
    print(portconf.get_ports_config())
    portconf.check_port_available('86:00.0')

    # example for global virtualization configuration file
    virtconf = VirtConf(VIRTCONF)
    virtconf.load_virt_config('LIBVIRT')
    print(virtconf.get_virt_config())

    # example for crbs configuration file
    crbsconf = CrbsConf(CRBCONF)
    print(crbsconf.load_crbs_config())

    # example for suite configure file
    suiteconf = SuiteConf("suite_sample")
    print(suiteconf.load_case_config("case1"))
    print(suiteconf.load_case_config("case2"))
