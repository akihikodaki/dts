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

import re
from crb import Crb
from config import PortConf, PORTCONF
from exception import PortConfigParseException
from utils import GREEN
from net_device import NetDevice

DEF_PASSWD = 's'
TP_BINARY = 'TestPoint'

FUNC_RULES = [
            # disable cut through for jumbo frame case
            'set port config 20,22 tx_cut_through off',
            # disable mac learning
            'set port config 0..22 learning off',
            #redirect PEP0 to EPL0
            'create acl 0',
            'create acl-rule 0 0',
            'add acl-rule condition 0 0 src-port 20',
            'add acl-rule action 0 0 redirect 1',
            'add acl-rule action 0 0 count',
            #redirect PEP1 to EPL1
            'create acl 1',
            'create acl-rule 1 0',
            'add acl-rule condition 1 0 src-port 22',
            'add acl-rule action 1 0 redirect 5',
            'add acl-rule action 1 0 count',
            'apply acl',
           ]

PERF_RULES = [
             'set port config 0..11 parser_cfg L4', # frame parser up to L4
             # good for performance
             'set api attribute boolean api.paritySweeper.enable false',
             'reg dbg set 0 CM_SOFTDROP_WM 0x5f005f00 0 0',
             'reg dbg set 0 CM_SHARED_WM 0x5f00 0 0',
             # rule for direct rx traffic
             # mac filter will be useless, so only enable for perf
             'create acl-rule 0 1',
             'add acl-rule condition 0 1 src-port 1',
             'add acl-rule action 0 1 redirect 20',
             'add acl-rule action 0 1 count',
             'create acl-rule 1 1',
             'add acl-rule condition 1 1 src-port 5',
             'add acl-rule action 1 1 redirect 22',
             'add acl-rule action 1 1 count',
             'apply acl',
           ]

class CtrlCrb(Crb):
    """
    Simplified Crb class for  RedRockCanyou control session
    """

    def __init__(self, crb):
        self.crb = crb
        self.NAME = 'dut_RRC_CONTROL'
        super(CtrlCrb, self).__init__(crb, None, self.NAME)

    def get_ip_address(self):
        return self.crb['IP']

    def get_password(self):
        return self.crb['pass']


class RedRockCanyou(NetDevice):
    """
    Class for RedRockCanyou, inherit from NetDevice class
    """

    def __init__(self, host, domain_id, bus_id, devfun_id):
        super(RedRockCanyou, self).__init__(host, domain_id, bus_id, devfun_id)

        self.tp_path = "~"
        self.sec_port = False
        self.host = host

        # load port config
        portconf = PortConf(PORTCONF)
        portconf.load_ports_config(host.crb['IP'])
        pci_addr = ':'.join((domain_id, bus_id, devfun_id))
        if not portconf.check_port_available(pci_addr):
            raise PortConfigParseException("RRC must configured")

        port_cfg = portconf.get_ports_config()[pci_addr]

        # secondary port do not need reinitialize
        if 'sec_port' in port_cfg.keys():
            print GREEN("Skip init second port test point session")
            if 'first_port' not in port_cfg.keys():
                raise PortConfigParseException("RRC second port must configure first port")
            # find net_device by pci_addr
            first_addr = port_cfg['first_port']
            port_info = self.host.get_port_info(first_addr)
            if port_info is None:
                raise PortConfigParseException("RRC first port not found")
            # get additional session
            netdev = port_info['port']
            self.ctrl_crb = netdev.get_control()
            self.sec_port = True
            return

        if 'tp_ip' not in port_cfg.keys():
            raise PortConfigParseException("RRC must configure test point ip")

        crb = {}
        crb['IP'] = port_cfg['tp_ip']
        if 'passwd' not in port_cfg.keys():
            crb['pass'] = DEF_PASSWD
        else:
            crb['pass'] = port_cfg['passwd']

        if 'tp_path' in port_cfg.keys():
            self.tp_path = port_cfg['tp_path']

        # create additional session
        self.ctrl_crb = CtrlCrb(crb)

    def setup(self):
        # setup function should be called after bind to igb_uio
        self.start_testpoint()

    def optimize_perf(self, peer0="", peer1=""):
        # rule which can optimize performance
        if self.sec_port is False:
            # applied rules
            for rule in PERF_RULES:
                self.ctrl_crb.send_expect("%s" %rule, "<0>%")
            # add default mac rule
            self.ctrl_crb.send_expect("add mac %s 1 locked port 1" % peer0, "<0>%")
            self.ctrl_crb.send_expect("add mac %s 1 locked port 5" % peer1, "<0>%")

    def stop(self):
        # second port do not need any operation
        if self.sec_port:
            return

        # stop testpoint
        self.stop_testpoint()

    def close(self):
        # second port do not need any operation
        if self.sec_port:
            return

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
        if self.sec_port:
            print GREEN("Skip start second port testpoint")
            return
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
        if self.sec_port:
            self.ctrl_crb.send_expect("add vlan port %d 5,22" % vlan_id, "<0>%")
        else:
            self.ctrl_crb.send_expect("add vlan port %d 1,20" % vlan_id, "<0>%")
    
    def delete_vlan(self, vlan_id=0):
        if self.sec_port:
            self.ctrl_crb.send_expect("del vlan port %d 5,22" % vlan_id, "<0>%")
        else:
            self.ctrl_crb.send_expect("del vlan port %d 1,20" % vlan_id, "<0>%")
        self.ctrl_crb.send_expect("del vlan %d" % vlan_id, "<0>%")

    def add_txvlan(self, vlan_id=0):
        if self.sec_port:
            self.ctrl_crb.send_expect("set vlan tagging %d 5 tag" % vlan_id, "<0>%")
        else:
            self.ctrl_crb.send_expect("set vlan tagging %d 1 tag" % vlan_id, "<0>%")

    def delete_txvlan(self, vlan_id=0):
        if self.sec_port:
            self.ctrl_crb.send_expect("set vlan tagging %d 5 untag" % vlan_id, "<0>%")
        else:
            self.ctrl_crb.send_expect("set vlan tagging %d 1 untag" % vlan_id, "<0>%")

    def enable_jumbo(self, framesize=0):
        if self.sec_port:
            self.ctrl_crb.send_expect("set port config 5 max_frame_size %d" % framesize, "<0>%")
        else:
            self.ctrl_crb.send_expect("set port config 1 max_frame_size %d" % framesize, "<0>%")

    def get_glortid_bymac(self, dmac):
        out = self.ctrl_crb.send_expect("show mac table all", "<0>%")
        pattern = r"([0-9a-f]{2}:){5}([0-9a-f]{2})"
        s = re.compile(pattern)
        res = s.search(dmac)
        if res is None:
            print "search none mac filter"
            return None
        else:
            mac_filter = res.group(2)
        pattern = r"(?<=%s)+([\sA-Za-z0-9/])+([0-9]{4})" %mac_filter
        s = re.compile(pattern)
        res = s.search(out)
        if res is None:
            print "search none port value"
            return None
        else:
            port_value = res.group(2)
        out = self.ctrl_crb.send_expect("show stacking logical-port all", "<0>%")
        pattern = r"([0-9a-z]{6})+(\s)+(%s)+" %port_value
        s = re.compile(pattern)
        res = s.search(out)
        if res is None:
            print "search none port glort id"
            return None
        else:
            port_glortid = res.group(1)
            return port_glortid

