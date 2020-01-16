# BSD LICENSE
#
# Copyright(c) 2010-2016 Intel Corporation. All rights reserved.
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

from crb import Crb
from config import PortConf, PORTCONF
from exception import PortConfigParseException
from utils import GREEN
from net_device import NetDevice
from dts import drivername

TP_BINARY = 'TestPoint'

FUNC_RULES = [
            # disable cut through for jumbo frame case
            'set port config 1,2 tx_cut_through off',
            # disable mac learning
            'set port config 0..2 learning off',
            #redirect PEP0 to EPL0
            'create acl 0',
            'create acl-rule 0 0',
            'add acl-rule condition 0 0 src-port 0',
            'add acl-rule action 0 0 redirect 1',
            'add acl-rule action 0 0 count',
            'apply acl',
           ]

PERF_RULES = [
             'set port config 0..1 parser_cfg L4', # frame parser up to L4
             # good for performance
             'set api attribute boolean api.paritySweeper.enable false',
             'reg dbg set 0 CM_SOFTDROP_WM 0x5f005f00 0 0',
             'reg dbg set 0 CM_SHARED_WM 0x5f00 0 0',
           ]

class CtrlCrb(Crb):
    """
    Simplified Crb class for  RedRockCanyou control session
    """

    def __init__(self, crb):
        self.crb = crb
        self.NAME = 'dut_atwood_control'
        super(CtrlCrb, self).__init__(crb, None, self.NAME)

    def get_ip_address(self):
        return self.crb['IP']

    def get_password(self):
        return self.crb['pass']


class Atwood(NetDevice):
    """
    Class for RedRockCanyou, inherit from NetDevice class
    """

    def __init__(self, host, domain_id, bus_id, devfun_id):
        super(Atwood, self).__init__(host, domain_id, bus_id, devfun_id)
        self.tp_path = "~"
        self.host = host

        # load port config
        portconf = PortConf(PORTCONF)
        portconf.load_ports_config(host.crb['IP'])
        pci_addr = ':'.join((domain_id, bus_id, devfun_id))
        if not portconf.check_port_available(pci_addr):
            raise PortConfigParseException("Atwood must configured")

        port_cfg = portconf.get_ports_config()[pci_addr]

        if 'tp_ip' not in list(port_cfg.keys()):
            raise PortConfigParseException("Atwood must configure test point ip")
        if 'passwd' not in list(port_cfg.keys()):
            raise PortConfigParseException("Atwood must configure host password")

        crb = {}
        crb['IP'] = port_cfg['tp_ip']
        crb['pass'] = port_cfg['passwd']

        if 'tp_path' in list(port_cfg.keys()):
            self.tp_path = port_cfg['tp_path']

        # create additional session
        self.ctrl_crb = CtrlCrb(crb)

    def setup(self):
        # setup function should be called after bind to igb_uio
        self.bind_driver(driver=drivername)
        self.start_testpoint()

    def optimize_perf(self, peer=""):
        pass

    def stop(self):
        # stop testpoint
        self.stop_testpoint()

    def close(self):
        # close session
        if self.ctrl_crb.session:
            self.ctrl_crb.session.close()
            self.ctrl_crb.session = None
        if self.ctrl_crb.alt_session:
            self.ctrl_crb.alt_session.close()
            self.ctrl_crb.alt_session = None

    def start_testpoint(self):
        """
        Before any execution, must enable test point first
        """
        self.ctrl_crb.send_expect("cd %s" % self.tp_path, "# ")
        if self.tp_path != "~":
            command = './' + TP_BINARY
        else:
            command = TP_BINARY

        self.ctrl_crb.send_expect("%s" % command, "<0>%", 120)
        for rule in FUNC_RULES:
            self.ctrl_crb.send_expect("%s" %rule, "<0>%")

    def stop_testpoint(self):
        """
        Exit test point
        """
        self.ctrl_crb.send_expect("quit", "# ")

    def get_control(self):
        return self.ctrl_crb

    def add_vlan(self, vlan_id=0):
        self.ctrl_crb.send_expect("create vlan %d" % vlan_id, "<0>%")
        self.ctrl_crb.send_expect("add vlan port %d 0,1" % vlan_id, "<0>%")
    
    def delete_vlan(self, vlan_id=0):
        self.ctrl_crb.send_expect("del vlan port %d 0,1" % vlan_id, "<0>%")
        self.ctrl_crb.send_expect("del vlan %d" % vlan_id, "<0>%")

    def add_txvlan(self, vlan_id=0):
        self.ctrl_crb.send_expect("set vlan tagging %d 1 tag" % vlan_id, "<0>%")

    def delete_txvlan(self, vlan_id=0):
        self.ctrl_crb.send_expect("set vlan tagging %d 1 untag" % vlan_id, "<0>%")

    def enable_jumbo(self, framesize=0):
        self.ctrl_crb.send_expect("set port config 1 max_frame_size %d" % framesize, "<0>%")
