# BSD LICENSE
#
# Copyright(c) 2010-2019 Intel Corporation. All rights reserved.
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
import string
import time
from pprint import pformat

from ssh_connection import SSHConnection
from settings import SCAPY2IXIA
from logger import getLogger
from utils import (convert_int2ip, convert_ip2int,
                   convert_mac2long, convert_mac2str)

from pktgen_base import (PacketGenerator, PKTGEN_IXIA,
                         TRANSMIT_CONT, TRANSMIT_M_BURST, TRANSMIT_S_BURST)

from scapy.packet import Packet
from scapy.utils import wrpcap


class Ixia(SSHConnection):
    """
    IXIA performance measurement class.
    """

    def __init__(self, tester, ixiaPorts):
        self.tester = tester
        self.NAME = PKTGEN_IXIA
        self.logger = getLogger(self.NAME)
        super(Ixia, self).__init__(
                            self.get_ip_address(),
                            self.NAME,
                            self.tester.get_username(),
                            self.get_password())
        super(Ixia, self).init_log(self.logger)

        self.tcl_cmds = []
        self.chasId = None
        self.conRelation = {}

        ixiaRef = self.NAME
        if ixiaRef is None or ixiaRef not in ixiaPorts:
            return

        self.ixiaVersion = ixiaPorts[ixiaRef]["Version"]
        self.ports = ixiaPorts[ixiaRef]["Ports"]

        if ixiaPorts[ixiaRef].has_key('force100g'):
            self.enable100g = ixiaPorts[ixiaRef]['force100g']
        else:
            self.enable100g = 'disable'

        self.logger.info(self.ixiaVersion)
        self.logger.info(self.ports)

        self.tclServerIP = ixiaPorts[ixiaRef]["IP"]

        # prepare tcl shell and ixia library
        self.send_expect("tclsh", "% ")
        self.send_expect("source ./IxiaWish.tcl", "% ")
        self.send_expect("set ::env(IXIA_VERSION) %s" % self.ixiaVersion, "% ")
        out = self.send_expect("package req IxTclHal", "% ")
        self.logger.debug("package req IxTclHal return:" + out)
        if self.ixiaVersion in out:
            if not self.tcl_server_login():
                self.close()
                self.session = None
            for port in self.ports:
                port['speed'] = self.get_line_rate(self.chasId, port)
        # ixia port stream management table
        self.stream_index = {}
        self.stream_total = {}

    def get_line_rate(self, chasid, port):
        ixia_port = "%d %d %d" % (self.chasId, port['card'], port['port'])
        return self.send_expect("stat getLineSpeed %s" % ixia_port, '%')

    def get_ip_address(self):
        return self.tester.get_ip_address()

    def get_password(self):
        return self.tester.get_password()

    def add_tcl_cmd(self, cmd):
        """
        Add one tcl command into command list.
        """
        self.tcl_cmds.append(cmd)

    def add_tcl_cmds(self, cmds):
        """
        Add one tcl command list into command list.
        """
        self.tcl_cmds += cmds

    def clean(self):
        """
        Clean ownership of IXIA devices and logout tcl session.
        """
        self.send_expect("clearOwnershipAndLogout", "% ")
        self.close()

    def parse_pcap(self, fpcap):
        # save Packet instance to pcap file
        if isinstance(fpcap, Packet):
            pcap_path = '/root/temp.pcap'
            if os.path.exists(pcap_path):
                os.remove(pcap_path)
            wrpcap(pcap_path, fpcap)
        else:
            pcap_path = fpcap

        dump_str1 = "cmds = []\n"
        dump_str2 = "for i in rdpcap('%s', -1):\n" % pcap_path
        dump_str3 = "    if 'VXLAN' in i.command():\n" + \
                    "        vxlan_str = ''\n" + \
                    "        l = len(i[VXLAN])\n" + \
                    "        vxlan = str(i[VXLAN])\n" + \
                    "        first = True\n" + \
                    "        for j in range(l):\n" + \
                    "            if first:\n" + \
                    "                vxlan_str += \"VXLAN(hexval='%02X\" %ord(vxlan[j])\n" + \
                    "                first = False\n" + \
                    "            else:\n" + \
                    "                vxlan_str += \" %02X\" %ord(vxlan[j])\n" + \
                    "        vxlan_str += \"\')\"\n" + \
                    "        command = re.sub(r\"VXLAN(.*)\", vxlan_str, i.command())\n" + \
                    "    else:\n" + \
                    "        command = i.command()\n" + \
                    "    cmds.append(command)\n" + \
                    "print(cmds)\n" + \
                    "exit()"

        f = open("dumppcap.py", "w")
        f.write(dump_str1)
        f.write(dump_str2)
        f.write(dump_str3)
        f.close()

        self.session.copy_file_to("dumppcap.py")
        out = self.send_expect("scapy -c dumppcap.py 2>/dev/null", "% ", 120)
        flows = eval(out)
        return flows

    def macToTclFormat(self, macAddr):
        """
        Convert normal mac address format into IXIA's format.
        """
        macAddr = macAddr.upper()
        return "%s %s %s %s %s %s" % (
                                macAddr[:2], macAddr[3:5], macAddr[6:8],
                                macAddr[9:11], macAddr[12:14], macAddr[15:17])

    def set_ether_fields(self, fields, default_fields):
        """
        Configure Ether protocol field value.
        """
        addr_mode = {
            # decrement the MAC address for as many numSA/numDA specified
            'dec':      'decrement',
            # increment the MAC address for as many numSA/numDA specified
            'inc':      'increment',
            # Generate random destination MAC address for each frame
            'random':   'ctrRandom',
            # set RepeatCounter mode to be idle as default
            'default':  'idle'}

        cmds = []
        for name, config in fields.iteritems():
            default_config = default_fields.get(name)
            mac_start = config.get('start') or default_config.get('start')
            mac_end = config.get('end')
            step = config.get('step') or 1
            action = config.get('action') or default_config.get('action')
            prefix = 'sa' if name == 'src' else 'da'
            if action == 'dec' and mac_end:
                cmds.append('stream config -{0} "{1}"'.format(
                                                            prefix, mac_end))
            else:
                cmds.append('stream config -{0} "{1}"'.format(
                                                            prefix, mac_start))
            if step:
                cmds.append('stream config -{0}Step {1}'.format(prefix, step))
            if action:
                cmds.append('stream config -{0}RepeatCounter {1}'.format(
                                                prefix, addr_mode.get(action)))
            if mac_end:
                mac_start_int = convert_mac2long(mac_start)
                mac_end_int = convert_mac2long(mac_end)
                flow_num = mac_end_int - mac_start_int + 1
                if flow_num <= 0:
                    msg = "end mac should not be bigger than start mac"
                    raise Exception(msg)
            else:
                flow_num = None

            if flow_num:
                cmds.append('stream config -num{0} {1}'.format(
                                                prefix.upper(), flow_num))
            # clear default field after it has been set
            default_fields.pop(name)
        # if some filed not set, set it here
        if default_fields:
            for name, config in default_fields.iteritems():
                ip_start = config.get('start')
                prefix = 'sa' if name == 'src' else 'da'
                cmds.append('stream config -{0} "{1}"'.format(prefix, ip_start))

        return cmds

    def ether(self, port, vm, src, dst, type):
        """
        Configure Ether protocol.
        """
        fields = vm.get('mac')
        srcMac = self.macToTclFormat(src)
        dstMac = self.macToTclFormat(dst)
        # common command setting
        self.add_tcl_cmd("protocol config -ethernetType ethernetII")
        cmds = []
        # if vm has been set, pick pcap fields' as default value
        if fields:
            default_fields = {
                'src': { 'action': 'default', 'start': src,},
                'dst': { 'action': 'default', 'start': dst,},}
            # set custom setting for field actions
            cmds = self.set_ether_fields(fields, default_fields)
            # set them in tcl commands group
            self.add_tcl_cmds(cmds)
        else:
            self.add_tcl_cmd('stream config -sa "%s"' % srcMac)
            self.add_tcl_cmd('stream config -da "%s"' % dstMac)

    def set_ip_fields(self, fields, default_fields):
        addr_mode = {
            # increment the host portion of the IP address for as many
            # IpAddrRepeatCount specified
            'dec':      'ipDecrHost',
            # increment the host portion of the IP address for as many
            # IpAddrRepeatCount specified
            'inc':      'ipIncrHost',
            # Generate random IP addresses
            'random':   'ipRandom',
            # no change to IP address regardless of IpAddrRepeatCount
            'idle':     'ipIdle',
            # set default
            'default':  'ipIdle',}
        cmds = []
        for name, config in fields.iteritems():
            default_config = default_fields.get(name)
            fv_name = 'IP.{0}'.format(name)
            ip_start = config.get('start') or default_config.get('start')
            ip_end = config.get('end')
            if ip_end:
                ip_start_int = convert_ip2int(ip_start)
                ip_end_int = convert_ip2int(ip_end)
                flow_num = ip_end_int - ip_start_int + 1
                if flow_num <= 0:
                    msg = "end ip address parameter is wrong"
                    raise Exception(msg)
            else:
                flow_num = None

            mask =  config.get('mask')
            _step = config.get('step')
            step = int(_step) if _step and isinstance(_step, (str, unicode)) else \
                   _step or 1
            action = config.get('action')
            # get ixia command prefix
            prefix = 'source' if name == 'src' else 'dest'
            # set command
            if action == 'dec' and ip_end:
                cmds.append('ip config -{0}IpAddr "{1}"'.format(
                                                        prefix, ip_end))
            else:
                cmds.append('ip config -{0}IpAddr "{1}"'.format(
                                                        prefix, ip_start))
            if flow_num:
                cmds.append('ip config -{0}IpAddrRepeatCount {1}'.format(
                                                            prefix, flow_num))

            cmds.append('ip config -{0}IpAddrMode {1}'.format(
                                  prefix, addr_mode.get(action or 'default')))

            if mask:
                cmds.append("ip config -{0}IpMask '{1}'".format(prefix, mask))
            # clear default field after it has been set
            default_fields.pop(name)
        # if all fields are set
        if not default_fields:
            return cmds
        # if some filed not set, set it here
        for name, config in default_fields.iteritems():
            ip_start = config.get('start')
            prefix = 'source' if name == 'src' else 'dest'
            cmds.append('ip config -{0}IpAddr "{1}"'.format(prefix, ip_start))
            cmds.append('ip config -{0}IpAddrMode {1}'.format(
                                  prefix, addr_mode.get('default')))

        return cmds

    def ip(self, port, vm, frag, src, proto, tos, dst, chksum, len, version,
           flags, ihl, ttl, id, options=None):
        """
        Configure IP protocol.
        """
        fields = vm.get('ip')
        # common command setting
        self.add_tcl_cmd("protocol config -name ip")
        # if fields has been set
        if fields:
            # pick pcap fields' as default value
            default_fields = {
                'src': { 'action': 'default', 'start': src,},
                'dst': { 'action': 'default', 'start': dst,},}
            # set custom setting for field actions
            cmds = self.set_ip_fields(fields, default_fields)
            # append custom setting
            self.add_tcl_cmds(cmds)
        else:
            self.add_tcl_cmd('ip config -sourceIpAddr "%s"' % src)
            self.add_tcl_cmd('ip config -destIpAddr "%s"' % dst)
        # common command setting
        self.add_tcl_cmd("ip config -ttl %d" % ttl)
        self.add_tcl_cmd("ip config -totalLength %d" % len)
        self.add_tcl_cmd("ip config -fragment %d" % frag)
        self.add_tcl_cmd("ip config -ipProtocol {0}".format(proto))
        self.add_tcl_cmd("ip config -identifier %d" % id)
        self.add_tcl_cmd("stream config -framesize %d" % (len + 18))
        # set stream setting in port
        self.add_tcl_cmd("ip set %s" % port)

    def ipv6(self, port, vm, version, tc, fl, plen, nh, hlim, src, dst):
        """
        Configure IPv6 protocol.
        """
        self.add_tcl_cmd("protocol config -name ipV6")
        self.add_tcl_cmd('ipV6 setDefault')
        self.add_tcl_cmd('ipV6 config -destAddr "%s"' %
                                                self.ipv6_to_tcl_format(dst))
        self.add_tcl_cmd('ipV6 config -sourceAddr "%s"' %
                                                self.ipv6_to_tcl_format(src))
        self.add_tcl_cmd('ipV6 config -flowLabel %d' % fl)
        self.add_tcl_cmd('ipV6 config -nextHeader %d' % nh)
        self.add_tcl_cmd('ipV6 config -hopLimit %d' % hlim)
        self.add_tcl_cmd('ipV6 config -trafficClass %d' % tc)
        self.add_tcl_cmd("ipV6 clearAllExtensionHeaders")
        self.add_tcl_cmd("ipV6 addExtensionHeader %d" % nh)

        self.add_tcl_cmd("stream config -framesize %d" % (plen + 40 + 18))
        self.add_tcl_cmd("ipV6 set %s" % port)

    def udp(self, port, vm, dport, sport, len, chksum):
        """
        Configure UDP protocol.
        """
        self.add_tcl_cmd("udp setDefault")
        self.add_tcl_cmd("udp config -sourcePort %d" % sport)
        self.add_tcl_cmd("udp config -destPort %d" % dport)
        self.add_tcl_cmd("udp config -length %d" % len)
        self.add_tcl_cmd("udp set %s" % port)

    def vxlan(self, port, vm, hexval):
        self.add_tcl_cmd("protocolPad setDefault")
        self.add_tcl_cmd("protocol config -enableProtocolPad true")
        self.add_tcl_cmd("protocolPad config -dataBytes \"%s\"" % hexval)
        self.add_tcl_cmd("protocolPad set %s" % port)

    def tcp(self, port, vm, sport, dport, seq, ack, dataofs, reserved, flags,
            window, chksum, urgptr, options=None):
        """
        Configure TCP protocol.
        """
        self.add_tcl_cmd("tcp setDefault")
        self.add_tcl_cmd("tcp config -sourcePort %d" % sport)
        self.add_tcl_cmd("tcp config -destPort %d" % dport)
        self.add_tcl_cmd("tcp set %s" % port)

    def sctp(self, port, vm, sport, dport, tag, chksum):
        """
        Configure SCTP protocol.
        """
        self.add_tcl_cmd("tcp config -sourcePort %d" % sport)
        self.add_tcl_cmd("tcp config -destPort %d" % dport)
        self.add_tcl_cmd("tcp set %s" % port)

    def set_dot1q_fields(self, fields):
        '''
        Configure 8021Q protocol field name.
        '''
        addr_mode = {
            # The VlanID tag is decremented by step for repeat number of times
            'dec':      'vDecrement',
            # The VlanID tag is incremented by step for repeat number of times
            'inc':      'vIncrement',
            # Generate random VlanID tag for each frame
            'random':   'vCtrRandom',
            # No change to VlanID tag regardless of repeat
            'idle':     'vIdle',}
        cmds = []
        for name, config in fields.iteritems():
            fv_name = '8021Q.{0}'.format(name)
            vlan_start = config.get('start') or 0
            vlan_end = config.get('end') or 256
            if vlan_end:
                flow_num = vlan_end - vlan_start + 1
                if flow_num <= 0:
                    msg = "end vlan id parameter is wrong"
                    raise Exception(msg)
            else:
                flow_num = None
            step = config.get('step') or 1
            action = config.get('action')
            #------------------------------------------------
            # set command
            if step:
                cmds.append('vlan config -step {0}'.format(step))
            if flow_num:
                cmds.append('vlan config -repeat {0}'.format(flow_num))
            if action:
                cmds.append('vlan config -mode {0}'.format(
                                                        addr_mode.get(action)))
        return cmds

    def dot1q(self, port, vm, prio, id, vlan, type):
        """
        Configure 8021Q protocol.
        """
        fields = vm.get('vlan')
        # common command setting
        self.add_tcl_cmd("protocol config -enable802dot1qTag true")
        # if fields has been set
        if fields:
            # set custom setting for field actions
            cmds = self.set_dot1q_fields(fields)
            self.add_tcl_cmds(cmds)
        self.add_tcl_cmd("vlan config -vlanID %d" % vlan)
        self.add_tcl_cmd("vlan config -userPriority %d" % prio)
        # set stream in port
        self.add_tcl_cmd("vlan set %s" % port)

    def config_stream(self, fpcap, vm, port_index, rate_percent, stream_id=1,
                      latency=False):
        """
        Configure IXIA stream and enable multiple flows.
        """
        ixia_port = self.get_ixia_port(port_index)
        flows = self.parse_pcap(fpcap)
        if not flows:
            msg = "flow has no format, it should be one."
            raise Exception(msg)
        if len(flows) >= 2:
            msg = "flow contain more than one format, it should be one."
            raise Exception(msg)

        # set commands at first stream
        if stream_id == 1:
            self.add_tcl_cmd("ixGlobalSetDefault")
        # set burst stream if burst stream is required
        stream_config = vm.get('stream_config')
        transmit_mode = stream_config.get('transmit_mode') or TRANSMIT_CONT
        if transmit_mode == TRANSMIT_S_BURST:
            cmds = self.config_single_burst_stream(
                                    stream_config.get('txmode'), rate_percent)
            self.add_tcl_cmds(cmds)
        else:
            self.config_ixia_stream(
                rate_percent, self.stream_total.get(port_index), latency)

        pat = re.compile(r"(\w+)\((.*)\)")
        for flow in flows:
            for header in flow.split('/'):
                match = pat.match(header)
                params = eval('dict(%s)' % match.group(2))
                method_name = match.group(1)
                if method_name == 'VXLAN':
                    method = getattr(self, method_name.lower())
                    method(ixia_port, vm.get('fields_config', {}), **params)
                    break
                if method_name in SCAPY2IXIA:
                    method = getattr(self, method_name.lower())
                    method(ixia_port, vm.get('fields_config', {}), **params)
            self.add_tcl_cmd("stream set %s %d" % (ixia_port, stream_id))
            # only use one packet format in pktgen
            break

        # set commands at last stream
        if stream_id > 1:
            self.add_tcl_cmd("stream config -dma gotoFirst")
            self.add_tcl_cmd("stream set %s %d" % (ixia_port, stream_id))

    def config_single_burst_stream(self, txmode, rate_percent):
        """ configure burst stream. """
        gapUnits = {
        # (default) Sets units of time for gap to nanoseconds
        'ns': 'gapNanoSeconds',
        # Sets units of time for gap to microseconds
        'us': 'gapMicroSeconds',
        # Sets units of time for gap to milliseconds
        'm': 'gapMilliSeconds',
        # Sets units of time for gap to seconds
        's': 'gapSeconds',}
        pkt_count = 1
        burst_count = txmode.get('total_pkts', 32)
        frameType = txmode.get('frameType') or {}
        time_unit = frameType.get('type', 'ns')
        gapUnit = gapUnits.get(time_unit) \
                        if time_unit in gapUnits.keys() else gapUnits.get('ns')
        # The inter-stream gap is the delay in clock ticks between stream.
        # This delay comes after the receive trigger is enabled. Setting this
        # option to 0 means no delay. (default = 960.0)
        isg = frameType.get('isg', 100)
        # The inter-frame gap specified in clock ticks (default = 960.0).
        ifg = frameType.get('ifg', 100)
        # Inter-Burst Gap is the delay between bursts of frames in clock ticks
        # (see ifg option for definition of clock ticks). If the IBG is set to
        # 0 then the IBG is equal to the ISG and the IBG becomes disabled.
        # (default = 960.0)
        ibg = frameType.get('ibg', 100)
        frame_cmds = [
            "stream config -rateMode usePercentRate",
            "stream config -percentPacketRate %s" % rate_percent,
            "stream config -dma stopStream",
            "stream config -rateMode useGap",
            "stream config -gapUnit {0}".format(gapUnit),
            "stream config -numFrames {0}".format(pkt_count),
            "stream config -numBursts {0}".format(burst_count),
            "stream config -ifg {0}".format(ifg),
            "stream config -ifgType gapFixed",
#             "stream config -enableIbg true",   # reserve
#             "stream config -ibg {0}".format(ibg), # reserve
#             "stream config -enableIsg true", # reserve
#             "stream config -isg {0}".format(isg), # reserve
            "stream config -frameSizeType sizeFixed",]

        return frame_cmds

    def config_ixia_stream(self, rate_percent, total_flows, latency):
        """
        Configure IXIA stream with rate and latency.
        Override this method if you want to add custom stream configuration.
        """
        self.add_tcl_cmd("stream config -rateMode usePercentRate")
        self.add_tcl_cmd("stream config -percentPacketRate %s" % rate_percent)
        self.add_tcl_cmd("stream config -numFrames 1")
        if total_flows == 1:
            self.add_tcl_cmd("stream config -dma contPacket")
        else:
            self.add_tcl_cmd("stream config -dma advance")
        # request by packet Group
        if latency is not False:
            self.add_tcl_cmd("stream config -fir true")

    def tcl_server_login(self):
        """
        Connect to tcl server and take ownership of all the ports needed.
        """
        out = self.send_expect("ixConnectToTclServer %s" % self.tclServerIP,
                               "% ", 30)
        self.logger.debug("ixConnectToTclServer return:" + out)
        if out.strip()[-1] != '0':
            return False

        self.send_expect("ixLogin IxiaTclUser", "% ")

        out = self.send_expect("ixConnectToChassis %s" % self.tclServerIP,
                               "% ", 30)
        if out.strip()[-1] != '0':
            return False

        out = self.send_expect(
                    "set chasId [ixGetChassisID %s]" % self.tclServerIP, "% ")
        self.chasId = int(out.strip())

        self.send_expect("ixClearOwnership [list %s]" % string.join(
            ['[list %d %d %d]' % (self.chasId, item['card'], item['port'])
                for item in self.ports], ' '),
            "% ", 10)
        self.send_expect("ixTakeOwnership [list %s] force" % string.join(
            ['[list %d %d %d]' % (self.chasId, item['card'], item['port'])
                for item in self.ports], ' '),
            "% ", 10)

        return True

    def tcl_server_logout(self):
        """
        Disconnect to tcl server and make sure has been logged out.
        """
        self.send_expect("ixDisconnectFromChassis %s" % self.tclServerIP, "%")
        self.send_expect("ixLogout", "%")
        self.send_expect("ixDisconnectTclServer %s" % self.tclServerIP, "%")

    def config_port(self, pList):
        """
        Configure ports and make them ready for performance validation.
        """
        pl = list()
        for item in pList:
            ixia_port = "%d %d %d" % (self.chasId, item['card'], item['port'])
            self.add_tcl_cmd("port setFactoryDefaults %s" % ixia_port)
            # if the line rate is 100G and we need this port work in 100G mode,
            # we need to add some configure to make it so.
            if int(self.get_line_rate(self.chasId, item).strip()) == 100000 and \
               self.enable100g == 'enable':
                self.add_tcl_cmd("port config -ieeeL1Defaults 0")
                self.add_tcl_cmd("port config -autonegotiate false")
                self.add_tcl_cmd("port config -enableRsFec true")
                self.add_tcl_cmd("port set %d %d %d" % (
                                        self.chasId,item['card'], item['port']))

            pl.append('[list %d %d %d]' % (
                                       self.chasId, item['card'], item['port']))

        self.add_tcl_cmd("set portList [list %s]" % string.join(pl, ' '))

        self.add_tcl_cmd("ixClearTimeStamp portList")
        self.add_tcl_cmd("ixWritePortsToHardware portList")
        self.add_tcl_cmd("ixCheckLinkState portList")

    def set_ixia_port_list(self, pList):
        """
        Implement ports/streams configuration on specified ports.
        """
        self.add_tcl_cmd("set portList [list %s]" %
                string.join(['[list %s]' % ixia_port for ixia_port in pList], ' '))

    def send_ping6(self, pci, mac, ipv6):
        """
        Send ping6 packet from IXIA ports.
        """
        port = self.pci_to_port(pci)['card']
        ixia_port = "%d %d %d" % (self.chasId, port['card'], port['port'])
        self.send_expect("source ./ixTcl1.0/ixiaPing6.tcl", "% ")
        cmd = 'ping6 "%s" "%s" %s' % (self.ipv6_to_tcl_format(ipv6),
                                      self.macToTclFormat(mac), ixia_port)
        out = self.send_expect(cmd, "% ", 90)
        return out

    def ipv6_to_tcl_format(self, ipv6):
        """
        Convert normal IPv6 address to IXIA format.
        """
        ipv6 = ipv6.upper()
        singleAddr = ipv6.split(":")
        if '' == singleAddr[0]:
            singleAddr = singleAddr[1:]
        if '' in singleAddr:
            tclFormatAddr = ''
            addStr = '0:' * (8 - len(singleAddr)) + '0'
            for i in range(len(singleAddr)):
                if singleAddr[i] == '':
                    tclFormatAddr += addStr + ":"
                else:
                    tclFormatAddr += singleAddr[i] + ":"
            tclFormatAddr = tclFormatAddr[0:len(tclFormatAddr) - 1]
            return tclFormatAddr
        else:
            return ipv6

    def get_ports(self):
        """
        API to get ixia ports for dts `ports_info`
        """
        plist = list()
        if self.session is None:
            return plist

        for p in self.ports:
            plist.append({'type': 'ixia',
                          'pci': 'IXIA:%d.%d' % (p['card'], p['port'])})
        return plist

    def get_ixia_port_pci(self, port_id):
        ports_info = self.get_ports()
        pci = ports_info[port_id]['pci']
        return pci

    def pci_to_port(self, pci):
        """
        Convert IXIA fake pci to IXIA port.
        """
        ixia_pci_regex = "IXIA:(\d*).(\d*)"
        m = re.match(ixia_pci_regex, pci)
        if m is None:
            msg = "ixia port not found"
            self.logger.warning(msg)
            return {'card': -1, 'port': -1}

        return {'card': int(m.group(1)), 'port': int(m.group(2))}

    def get_ixia_port_info(self, port):
        if port == None or port >= len(self.ports):
            msg = "<{0}> exceed maximum ixia ports".format(port)
            raise Exception(msg)
        pci_addr = self.get_ixia_port_pci(port)
        port_info = self.pci_to_port(pci_addr)
        return port_info

    def get_ixia_port(self, port):
        port_info= self.get_ixia_port_info(port)
        ixia_port = "%d %d %d" % (self.chasId,
                                  port_info['card'], port_info['port'])
        return ixia_port

    def loss(self, portList, ratePercent, delay=5):
        """
        Run loss performance test and return loss rate.
        """
        rxPortlist, txPortlist = self._configure_everything(portList,
                                                            ratePercent)
        return self.get_loss_packet_rate(rxPortlist, txPortlist, delay)

    def get_loss_packet_rate(self, rxPortlist, txPortlist, delay=5):
        """
        Get RX/TX packet statistics and calculate loss rate.
        """
        time.sleep(delay)

        self.send_expect("ixStopTransmit portList", "%", 10)
        time.sleep(2)
        sendNumber = 0
        for port in txPortlist:
            self.stat_get_stat_all_stats(port)
            sendNumber += self.get_frames_sent()
            time.sleep(0.5)

        self.logger.info("send :%f" % sendNumber)

        assert sendNumber != 0

        revNumber = 0
        for port in rxPortlist:
            self.stat_get_stat_all_stats(port)
            revNumber += self.get_frames_received()
        self.logger.info("rev  :%f" % revNumber)

        return float(sendNumber - revNumber) / sendNumber, sendNumber, revNumber

    def latency(self, portList, ratePercent, delay=5):
        """
        Run latency performance test and return latency statistics.
        """
        rxPortlist, txPortlist = self._configure_everything(
                                                portList, ratePercent, True)
        return self.get_packet_latency(rxPortlist)

    def get_packet_latency(self, rxPortlist):
        """
        Stop IXIA transmit and return latency statistics.
        """
        latencyList = []
        time.sleep(10)
        self.send_expect("ixStopTransmit portList", "%", 10)
        for rx_port in rxPortlist:
            self.pktGroup_get_stat_all_stats(rx_port)
            latency = {"port": rx_port,
                       "min": self.get_min_latency(),
                       "max": self.get_max_latency(),
                       "average": self.get_average_latency()}
            latencyList.append(latency)
        return latencyList

    def throughput(self, port_list, rate_percent=100, delay=5):
        """
        Run throughput performance test and return throughput statistics.
        """
        rxPortlist, txPortlist = self._configure_everything(
                                                    port_list, rate_percent)
        return self.get_transmission_results(rxPortlist, txPortlist, delay)

    def is_packet_ordered(self, port_list, delay):
        """
        This function could be used to check the packets' order whether same as
        the receive sequence.

        Please notice that this function only support single-stream mode.
        """
        port = self.ports[0]
        ixia_port = "%d %d %d" % (self.chasId, port['card'], port['port'])
        rxPortlist, txPortlist = self.prepare_port_list(port_list)
        self.prepare_ixia_for_transmission(txPortlist, rxPortlist)
        self.send_expect('port config -receiveMode [expr $::portCapture|$::portRxSequenceChecking|$::portRxModeWidePacketGroup]', '%')
        self.send_expect('port config -autonegotiate true', '%')
        self.send_expect('ixWritePortsToHardware portList', '%')
        self.send_expect('set streamId 1', '%')
        self.send_expect('stream setDefault', '%')
        self.send_expect('ixStartPortPacketGroups %s' % ixia_port, '%')
        self.send_expect('ixStartTransmit portList', '%')
        # wait `delay` seconds to make sure link is up
        self.send_expect('after 1000 * %d' % delay, '%')
        self.send_expect('ixStopTransmit portList', '%')
        self.send_expect('ixStopPortPacketGroups %s' % ixia_port, '%')
        self.send_expect('packetGroupStats get %s 1 1' % ixia_port, '%')
        self.send_expect('packetGroupStats getGroup 1', '%')
        self.send_expect('set reverseSequenceError [packetGroupStats cget -reverseSequenceError]]', '%')
        output = self.send_expect('puts $reverseSequenceError', '%')
        return int(output[:-2])

    def _configure_everything(self, port_list, rate_percent, latency=False):
        """
        Prepare and configure IXIA ports for performance test.
        """
        rxPortlist, txPortlist = self.prepare_port_list(
                                            port_list, rate_percent, latency)
        self.prepare_ixia_for_transmission(txPortlist, rxPortlist)
        self.configure_transmission()
        self.start_transmission()
        self.clear_tcl_commands()
        return rxPortlist, txPortlist

    def clear_tcl_commands(self):
        """
        Clear all commands in command list.
        """
        del self.tcl_cmds[:]

    def start_transmission(self):
        """
        Run commands in command list.
        """
        fileContent = "\n".join(self.tcl_cmds) + "\n"
        self.tester.create_file(fileContent, 'ixiaConfig.tcl')
        self.send_expect("source ixiaConfig.tcl", "% ", 75)

    def configure_transmission(self, option=None):
        """
        Start IXIA ports transmission.
        """
        self.add_tcl_cmd("ixStartTransmit portList")

    def prepare_port_list(self, portList, rate_percent=100, latency=False):
        """
        Configure stream and flow on every IXIA ports.
        """
        txPortlist = set()
        rxPortlist = set()

        for subPortList in portList:
            txPort, rxPort = subPortList[:2]
            txPortlist.add(txPort)
            rxPortlist.add(rxPort)

        # port init
        self.config_port([self.get_ixia_port_info(port)
                                for port in txPortlist.union(rxPortlist)])

        # calculate total streams of ports
        for (txPort, rxPort, pcapFile, option) in portList:
            if txPort not in self.stream_total.keys():
                self.stream_total[txPort] = 1
            else:
                self.stream_total[txPort] += 1

        # stream/flow setting
        for (txPort, rxPort, pcapFile, option) in portList:
            if txPort not in self.stream_index.keys():
                self.stream_index[txPort] = 1
            frame_index = self.stream_index[txPort]
            self.config_stream(pcapFile, option, txPort,
                               rate_percent, frame_index, latency)
            self.stream_index[txPort] += 1
        # clear stream ids table
        self.stream_index.clear()
        self.stream_total.clear()

        # config stream before packetGroup
        if latency is not False:
            for subPortList in portList:
                txPort, rxPort = subPortList[:2]
                flow_num = len(self.parse_pcap(pcapFile))
                self.config_pktGroup_rx(self.get_ixia_port(rxPort))
                self.config_pktGroup_tx(self.get_ixia_port(txPort))
        return rxPortlist, txPortlist

    def prepare_ixia_for_transmission(self, txPortlist, rxPortlist):
        """
        Clear all statistics and implement configuration to IXIA hardware.
        """
        self.add_tcl_cmd("ixClearStats portList")
        self.set_ixia_port_list([self.get_ixia_port(port)
                                                 for port in txPortlist])
        self.add_tcl_cmd("ixWriteConfigToHardware portList")
        # Wait for changes to take affect and make sure links are up
        self.add_tcl_cmd("after 1000")
        for port in txPortlist:
            self.start_pktGroup(self.get_ixia_port(port))
        for port in rxPortlist:
            self.start_pktGroup(self.get_ixia_port(port))

    def hook_transmission_func(self):
        pass

    def get_transmission_results(self, rx_port_list, tx_port_list, delay=5):
        """
        Override this method if you want to change the way of getting results
        back from IXIA.
        """
        time.sleep(delay)
        bpsRate = 0
        rate = 0
        oversize = 0
        for port in rx_port_list:
            self.stat_get_rate_stat_all_stats(port)
            out = self.send_expect("stat cget -framesReceived", '%', 10)
            rate += int(out.strip())
            out = self.send_expect("stat cget -bitsReceived", '% ', 10)
            self.logger.debug("port %d bits rate:" % (port) + out)
            bpsRate += int(out.strip())
            out = self.send_expect("stat cget -oversize", '%', 10)
            oversize += int(out.strip())

        self.logger.info("Rate: %f Mpps" % (rate * 1.0 / 1000000))
        self.logger.info("Mbps rate: %f Mbps" % (bpsRate * 1.0 / 1000000))

        self.hook_transmission_func()

        self.send_expect("ixStopTransmit portList", "%", 30)

        if rate == 0 and oversize > 0:
            return (bpsRate, oversize)
        else:
            return (bpsRate, rate)

    def config_ixia_dcb_init(self, rxPort, txPort):
        """
        Configure Ixia for DCB.
        """
        self.send_expect("source ./ixTcl1.0/ixiaDCB.tcl", "% ")
        self.send_expect("configIxia %d %s" % (
                            self.chasId,
                            string.join(["%s" % (
                                repr(self.conRelation[port][n]))
                                    for port in [rxPort, txPort]
                                            for n in range(3)])),
                         "% ", 100)

    def config_port_dcb(self, direction, tc):
        """
        Configure Port for DCB.
        """
        self.send_expect("configPort %s %s" % (direction, tc), "% ", 100)

    def config_port_flow_control(self, ports, option):
        ''' configure the type of flow control on a port '''
        if not ports:
            return
        #  mac address, default is "01 80 C2 00 00 01"
        dst_mac = option.get('dst_mac') or "\"01 80 C2 00 00 01\""
        if not dst_mac:
            return
        pause_time = option.get('pause_time') or 255
        flow_ctrl_cmds = [
            "protocol setDefault",
            "port config -flowControl true",
            "port config -flowControlType ieee8023x"]
        for port in ports:
            ixia_port = self.get_ixia_port(port)
            flow_ctrl_cmds = [
                # configure a pause control packet.
                "port set {0}".format(ixia_port),
                "protocol config -name pauseControl",
                "pauseControl setDefault",
                "pauseControl config -pauseControlType ieee8023x",
                'pauseControl config -da "{0}"'.format(dst_mac),
                "pauseControl config -pauseTime {0}".format(pause_time),
                "pauseControl set {0}".format(ixia_port),]
        self.add_tcl_cmds(flow_ctrl_cmds)

    def cfgStreamDcb(self, stream, rate, prio, types):
        """
        Configure Stream for DCB.
        """
        self.send_expect("configStream %s %s %s %s" % (stream, rate, prio, types), "% ", 100)

    def get_connection_relation(self, dutPorts):
        """
        Get the connect relations between DUT and Ixia.
        """
        for port in dutPorts:
            info = self.tester.get_pci(self.tester.get_local_port(port)).split('.')
            self.conRelation[port] = [
                            int(info[0]), int(info[1]),
                            repr(self.tester.dut.get_mac_address(port).replace(':', ' ').upper())]
        return self.conRelation

    def config_pktGroup_rx(self, ixia_port):
        """
        Sets the transmit Packet Group configuration of the stream
        Default streamID is 1
        """
        self.add_tcl_cmd("port config -receiveMode $::portRxModeWidePacketGroup")
        self.add_tcl_cmd("port set %s" % ixia_port)
        self.add_tcl_cmd("packetGroup setDefault")
        self.add_tcl_cmd("packetGroup config -latencyControl cutThrough")
        self.add_tcl_cmd("packetGroup setRx %s" % ixia_port)
        self.add_tcl_cmd("packetGroup setTx %s 1" % ixia_port)

    def config_pktGroup_tx(self, ixia_port):
        """
        Configure tx port pktGroup for latency.
        """
        self.add_tcl_cmd("packetGroup setDefault")
        self.add_tcl_cmd("packetGroup config -insertSignature true")
        self.add_tcl_cmd("packetGroup setTx %s 1" % ixia_port)

    def start_pktGroup(self, ixia_port):
        """
        Start tx port pktGroup for latency.
        """
        self.add_tcl_cmd("ixStartPortPacketGroups %s" % ixia_port)

    def pktGroup_get_stat_all_stats(self, port_number):
        """
        Stop Packet Group operation on port and get current Packet Group
        statistics on port.
        """
        ixia_port = self.get_ixia_port(port_number)
        self.send_expect("ixStopPortPacketGroups %s" % ixia_port, "%", 100)
        self.send_expect("packetGroupStats get %s 0 16384" % ixia_port, "%", 100)
        self.send_expect("packetGroupStats getGroup 0", "%", 100)

    def close(self):
        """
        We first close the tclsh session opened at the beginning,
        then the SSH session.
        """
        if self.isalive():
            self.send_expect('exit', '# ')
            super(Ixia, self).close()

    def stat_get_stat_all_stats(self, port_number):
        """
        Sends a IXIA TCL command to obtain all the stat values on a given port.
        """
        ixia_port = self.get_ixia_port(port_number)
        command = 'stat get statAllStats {0}'.format(ixia_port)
        self.send_expect(command, '% ', 10)

    def prepare_ixia_internal_buffers(self, port_number):
        """
        Tells IXIA to prepare the internal buffers were the frames were captured.
        """
        ixia_port = self.get_ixia_port(port_number)
        command = 'capture get {0} {1} {2}'.format(ixia_port)
        self.send_expect(command, '% ', 30)

    def stat_get_rate_stat_all_stats(self, port_number):
        """
        All statistics of specified IXIA port.
        """
        ixia_port = self.get_ixia_port(port_number)
        command = 'stat getRate statAllStats {0}'.format(ixia_port)
        out = self.send_expect(command, '% ', 30)
        return out

    def ixia_capture_buffer(self, port_number, first_frame, last_frame):
        """
        Tells IXIA to load the captured frames into the internal buffers.
        """
        ixia_port = self.get_ixia_port(port_number)
        command = 'captureBuffer get {0} {1} {2}'.format(
                                ixia_port, first_frame, last_frame)
        self.send_expect(command, '%', 60)

    def ixia_export_buffer_to_file(self, frames_filename):
        """
        Tells IXIA to dump the frames it has loaded in its internal buffer to a
        text file.
        """
        command = 'captureBuffer export %s' % frames_filename
        self.send_expect(command, '%', 30)

    def _stat_cget_value(self, requested_value):
        """
        Sends a IXIA TCL command to obtain a given stat value.
        """
        command = "stat cget -" + requested_value
        result = self.send_expect(command, '%', 10)
        return int(result.strip())

    def _capture_cget_value(self, requested_value):
        """
        Sends a IXIA TCL command to capture certain number of packets.
        """
        command = "capture cget -" + requested_value
        result = self.send_expect(command, '%', 10)
        return int(result.strip())

    def _packetgroup_cget_value(self, requested_value):
        """
        Sends a IXIA TCL command to get pktGroup stat value.
        """
        command = "packetGroupStats cget -" + requested_value
        result = self.send_expect(command, '%', 10)
        return int(result.strip())

    def number_of_captured_packets(self):
        """
        Returns the number of packets captured by IXIA on a previously set
        port. Call self.stat_get_stat_all_stats(port) before.
        """
        return self._capture_cget_value('nPackets')

    def get_frames_received(self):
        """
        Returns the number of packets captured by IXIA on a previously set
        port. Call self.stat_get_stat_all_stats(port) before.
        """
        if self._stat_cget_value('framesReceived') != 0:
            return self._stat_cget_value('framesReceived')
        else:
            # if the packet size is large than 1518, this line will avoid return
            # a wrong number
            return self._stat_cget_value('oversize')

    def get_flow_control_frames(self):
        """
        Returns the number of control frames captured by IXIA on a
        previously set port. Call self.stat_get_stat_all_stats(port) before.
        """
        return self._stat_cget_value('flowControlFrames')

    def get_frames_sent(self):
        """
        Returns the number of packets sent by IXIA on a previously set
        port. Call self.stat_get_stat_all_stats(port) before.
        """
        return self._stat_cget_value('framesSent')

    def get_transmit_duration(self):
        """
        Returns the duration in nanosecs of the last transmission on a
        previously set port. Call self.stat_get_stat_all_stats(port) before.
        """
        return self._stat_cget_value('transmitDuration')

    def get_min_latency(self):
        """
        Returns the minimum latency in nanoseconds of the frames in the
        retrieved capture buffer. Call packetGroupStats get before.
        """
        return self._packetgroup_cget_value('minLatency')

    def get_max_latency(self):
        """
        Returns the maximum latency in nanoseconds of the frames in the
        retrieved capture buffer. Call packetGroupStats get before.
        """
        return self._packetgroup_cget_value('maxLatency')

    def get_average_latency(self):
        """
        Returns the average latency in nanoseconds of the frames in the
        retrieved capture buffer. Call packetGroupStats get before.
        """
        return self._packetgroup_cget_value('averageLatency')

    def _transmission_pre_config(self, port_list, rate_percent, latency=False):
        """
        Prepare and configure IXIA ports for performance test. And remove the
        transmission step in this config sequence.

        This function is set only for function send_number_packets for
        nic_single_core_perf test case use
        """
        rxPortlist, txPortlist = self.prepare_port_list(
                                            port_list, rate_percent, latency)
        self.prepare_ixia_for_transmission(txPortlist, rxPortlist)
        self.start_transmission()
        self.clear_tcl_commands()
        return rxPortlist, txPortlist

    def send_number_packets(self, portList, ratePercent, packetNum):
        """
        Configure ixia to send fixed number of packets
        Note that this function is only set for test_suite nic_single_core_perf,
        Not for common use
        """
        rxPortlist, txPortlist = self._transmission_pre_config(portList,
                                                               ratePercent)

        self.send_expect("stream config -numFrames %s" % packetNum, "%", 5)
        self.send_expect("stream config -dma stopStream", "%", 5)
        for txPort in txPortlist:
            ixia_port = self.get_ixia_port(txPort)
            self.send_expect("stream set %s 1" % ixia_port, "%", 5)

        self.send_expect("ixWritePortsToHardware portList", "%", 5)
        self.send_expect("ixClearStats portList", "%", 5)
        self.send_expect("ixStartTransmit portList", "%", 5)
        time.sleep(10)

        rxPackets = 0
        for port in txPortlist:
            self.stat_get_stat_all_stats(port)
            txPackets = self.get_frames_sent()
            while txPackets != packetNum:
                time.sleep(10)
                self.stat_get_stat_all_stats(port)
                txPackets = self.get_frames_sent()
            rxPackets += self.get_frames_received()
        self.logger.info("Received packets :%s" % rxPackets)

        return rxPackets

    #---------------------------------------------------------
    # extend methods for pktgen subclass `IxiaPacketGenerator
    #---------------------------------------------------------
    def disconnect(self):
        ''' quit from ixia server '''
        pass

    def start(self, **run_opt):
        ''' start ixia ports '''
        self.configure_transmission(run_opt)
        self.start_transmission()
        time.sleep(run_opt.get('duration') or 5)

    def remove_all_streams(self):
        ''' delete all streams on all ixia ports '''
        if not self.ports:
            return
        for item in self.ports:
            cmd = 'port reset {0} {1} {2}'.format(
                                self.chasId, item['card'], item['port'])
            self.send_expect(cmd, "%", 10)

    def reset(self, ports=None):
        ''' reset ixia configuration for ports '''
        pass

    def clear_tcl_buffer(self):
        ''' clear tcl commands buffer '''
        self.tcl_cmds = []

    def clear_stats(self):
        pass

    def stop_transmit(self):
        '''
        Stop IXIA transmit
        '''
        time.sleep(2)
        self.send_expect("ixStopTransmit portList", "%", 40)

    def get_latency_stat(self, port_list):
        """
        get latency statistics.
        """
        stats = {}
        for port in port_list:
            self.pktGroup_get_stat_all_stats(port)
            stats[port] = {
                'average': self.get_average_latency(),
                'total_max': self.get_max_latency(),
                'total_min': self.get_min_latency()}
        return stats

    def get_loss_stat(self, port_list):
        """
        Get RX/TX packet statistics.
        """
        stats = {}
        for port in port_list:
            self.stat_get_stat_all_stats(port)
            stats[port] = {
                'ibytes': 0,
                'ierrors': 0,
                'ipackets': self.get_frames_received(),
                'obytes': 0,
                'oerrors': 0,
                'opackets': self.get_frames_sent(),
                'rx_bps': 0,
                'rx_pps': 0,
                'tx_bps': 0,
                'tx_pps': 0,}
            time.sleep(0.5)
        return stats

    def get_throughput_stat(self, port_list):
        """
        Get RX transmit rate.
        """
        stats = {}
        for port in port_list:
            self.stat_get_rate_stat_all_stats(port)
            out = self.send_expect("stat cget -framesReceived", '%', 10)
            rate = int(out.strip())
            out = self.send_expect("stat cget -bitsReceived", '% ', 10)
            bpsRate = int(out.strip())
            out = self.send_expect("stat cget -oversize", '%', 10)
            oversize = int(out.strip())
            rate = oversize if rate == 0 and oversize > 0 else rate

            stats[port] = {
                'ibytes': 0,
                'ierrors': 0,
                'ipackets': 0,
                'obytes': 0,
                'oerrors': 0,
                'opackets': 0,
                'rx_bps': bpsRate,
                'rx_pps': rate,
                'tx_bps': 0,
                'tx_pps': 0,}

        return stats

    def get_stats(self, ports, mode):
        '''
        get statistics of custom mode
        '''
        methods = {
            'throughput':   self.get_throughput_stat,
            'loss':         self.get_loss_stat,
            'latency':      self.get_latency_stat,}
        if mode not in methods.keys():
            msg = "not support mode <{0}>".format(mode)
            raise Exception(msg)
        # get custom mode stat
        func = methods.get(mode)
        stats = func(ports)

        return stats


class IxiaPacketGenerator(PacketGenerator):
    """
    Ixia packet generator
    """
    def __init__(self, tester):
        # ixia management
        self.pktgen_type = PKTGEN_IXIA
        self._conn = None
        # ixia configuration information of dts
        conf_inst = self._get_generator_conf_instance()
        self.conf = conf_inst.load_pktgen_config()
        # ixia port configuration
        self._traffic_opt = {}
        self._traffic_ports = []
        self._ports = []
        self._rx_ports = []
        # statistics management
        self.runtime_stats = {}
        # check configuration options
        self.options_keys = [
            'txmode', 'ip', 'vlan', 'transmit_mode', 'rate']
        self.ip_keys = ['start', 'end','action', 'step', 'mask',]
        self.vlan_keys = ['start', 'end', 'action', 'step', 'count',]

        super(IxiaPacketGenerator, self).__init__(tester)
        self.tester = tester

    def get_ports(self):
        ''' only used for ixia packet generator '''
        return self._conn.get_ports()

    def _prepare_generator(self):
        ''' start ixia server '''
        try:
            self._connect(self.tester, self.conf)
        except Exception as e:
            msg = "failed to connect to ixia server"
            raise Exception(msg)

    def _connect(self, tester, conf):
        # initialize ixia class
        self._conn = Ixia(tester, conf)
        for p in self._conn.get_ports():
            self._ports.append(p)

        self.logger.debug(self._ports)

    def _disconnect(self):
        '''
        disconnect with ixia server
        '''
        try:
            self._remove_all_streams()
            self._conn.disconnect()
        except Exception as e:
            msg = 'Error disconnecting: %s' % e
            self.logger.error(msg)
        self._conn = None

    def _get_port_pci(self, port_id):
        '''
        get ixia port pci address
        '''
        for pktgen_port_id, info in enumerate(self._ports):
            if pktgen_port_id == port_id:
                _pci = info.get('pci')
                return _pci
        else:
            return None

    def _get_gen_port(self, pci):
        '''
        get port management id of the packet generator
        '''
        for pktgen_port_id, info in enumerate(self._ports):
            _pci = info.get('pci')
            if _pci == pci:
                return pktgen_port_id
        else:
            return -1

    def _is_gen_port(self, pci):
        '''
        check if a pci address is managed by the packet generator
        '''
        for name, _port_obj in self._conn.ports.iteritems():
            _pci = _port_obj.info['pci_addr']
            self.logger.info((_pci, pci))
            if _pci == pci:
                return True
        else:
            return False

    def _get_ports(self):
        """
        Return self ports information
        """
        ports = []
        for idx in range(len(self._ports)):
            ports.append('IXIA:%d' % idx)
        return ports

    @property
    def _vm_conf(self):
        # close it and wait for more discussion about pktgen framework
        return None
        conf = {}
        #get the subnet range of src and dst ip
        if self.conf.has_key("ip_src"):
            conf['src'] = {}
            ip_src = self.conf['ip_src']
            ip_src_range = ip_src.split('-')
            conf['src']['start'] = ip_src_range[0]
            conf['src']['end'] = ip_src_range[1]

        if self.conf.has_key("ip_dst"):
            conf['dst'] = {}
            ip_dst = self.conf['ip_dst']
            ip_dst_range = ip_dst.split('-')
            conf['dst']['start'] = ip_dst_range[0]
            conf['dst']['end'] = ip_dst_range[1]

        return conf if conf else None

    def _clear_streams(self):
        ''' clear streams in `PacketGenerator` '''
        # if streams has been attached, remove them from trex server.
        self._remove_all_streams()

    def _remove_all_streams(self):
        '''
        remove all stream deployed on the packet generator
        '''
        if not self.get_streams():
            return
        self._conn.remove_all_streams()

    def _get_port_features(self, port_id):
        ''' get ports features '''
        ports = self._conn.ports
        if port_id not in ports:
            return None
        features = self._conn.ports[port_id].get_formatted_info()

        return features

    def _is_support_flow_control(self, port_id):
        ''' check if a port support flow control '''
        features = self._get_port_features(port_id)
        if not features or features.get('fc_supported') == 'no':
            return False
        else:
            return True

    def _preset_ixia_port(self):
        ''' set ports flow_ctrl attribute '''
        rx_ports = self._rx_ports
        flow_ctrl_opt = self._traffic_opt.get('flow_control')
        if not flow_ctrl_opt:
            return
        # flow control of port running trex traffic
        self._conn.config_port_flow_control(rx_ports, flow_ctrl_opt)

    def _throughput_stats(self, stream, stats):
        ''' convert ixia throughput statistics format to dts PacketGenerator format '''
        # tx packet
        tx_port_id = stream["tx_port"]
        port_stats = stats.get(tx_port_id)
        if not port_stats:
            msg = "failed to get tx_port {0} statistics".format(tx_port_id)
            raise Exception(msg)
        tx_bps = port_stats.get("tx_bps")
        tx_pps = port_stats.get("tx_pps")
        msg = [
            "Tx Port %d stats: " % (tx_port_id),
            "tx_port: %d,  tx_bps: %f, tx_pps: %f " % (
                                            tx_port_id, tx_bps, tx_pps)]
        self.logger.info(pformat(port_stats))
        self.logger.info(os.linesep.join(msg))
        # rx bps/pps
        rx_port_id = stream["rx_port"]
        port_stats = stats.get(rx_port_id)
        if not port_stats:
            msg = "failed to get rx_port {0} statistics".format(rx_port_id)
            raise Exception(msg)
        rx_bps = port_stats.get("rx_bps")
        rx_pps = port_stats.get("rx_pps")
        msg = [
            "Rx Port %d stats: " % (rx_port_id),
            "rx_port: %d,  rx_bps: %f, rx_pps: %f" % (
                                        rx_port_id, rx_bps, rx_pps)]

        self.logger.info(pformat(port_stats))
        self.logger.info(os.linesep.join(msg))

        return rx_bps, rx_pps

    def _loss_rate_stats(self, stream, stats):
        ''' convert ixia loss rate statistics format to dts PacketGenerator format '''
        # tx packet
        port_id = stream.get("tx_port")
        if port_id in stats.keys():
            port_stats = stats[port_id]
        else:
            msg = "port {0} statistics is not found".format(port_id)
            self.logger.error(msg)
            return None
        msg = "Tx Port %d stats: " % (port_id)
        self.logger.info(msg)
        opackets = port_stats["opackets"]
        # rx packet
        port_id = stream.get("rx_port")
        port_stats = stats[port_id]
        msg = "Rx Port %d stats: " % (port_id)
        self.logger.info(msg)
        ipackets = port_stats["ipackets"]

        return opackets, ipackets

    def _latency_stats(self, stream, stats):
        ''' convert ixia latency statistics format to dts PacketGenerator format '''
        port_id = stream.get("tx_port")
        if port_id in stats.keys():
            port_stats = stats[port_id]
        else:
            msg = "port {0} latency stats is not found".format(port_id)
            self.logger.error(msg)
            return None

        latency_stats = {
            'min':    port_stats.get('total_min'),
            'max':    port_stats.get('total_max'),
            'average':port_stats.get('average'),}

        return latency_stats

    def send_ping6(self, pci, mac, ipv6):
        ''' Send ping6 packet from IXIA ports. '''
        return self._conn.send_ping6(pci, mac, ipv6)

    ##########################################################################
    #
    #  class ``PacketGenerator`` abstract methods should be implemented here
    #
    ##########################################################################
    def _prepare_transmission(self, stream_ids=[], latency=False):
        ''' add one/multiple streams in one/multiple ports '''
        port_config = {}

        for stream_id in stream_ids:
            stream = self._get_stream(stream_id)
            tx_port = stream.get('tx_port')
            rx_port = stream.get('rx_port')
            pcap_file = stream.get('pcap_file')
            rate_percent = stream.get('rate')
            # save port id list
            if tx_port not in self._traffic_ports:
                self._traffic_ports.append(tx_port)
            if rx_port not in self._traffic_ports:
                self._traffic_ports.append(rx_port)
            if rx_port not in self._rx_ports:
                self._rx_ports.append(rx_port)
            # set all streams in one port to do batch configuration
            options = stream['options']
            if tx_port not in port_config.keys():
                port_config[tx_port] = []
            config = {}
            config.update(options)
            # In pktgen, all streams flow control option are the same by design.
            self._traffic_opt['flow_control'] = options.get('flow_control') or {}
            # if vm config by pktgen config file, set it here to take the place
            # of setting on suite
            if self._vm_conf: # TBD, remove this process later
                config['fields_config'] = self._vm_conf
            # get stream rate percent
            stream_config = options.get('stream_config')
            # set port list input parameter of ixia class
            ixia_option = [tx_port, rx_port, pcap_file, options]
            port_config[tx_port].append(ixia_option)

        if not port_config:
            msg = 'no stream options for ixia packet generator'
            raise Exception(msg)
        #-------------------------------------------------------------------
        port_lists = []
        for port_id, option in port_config.iteritems():
            port_lists += option
        self._conn.clear_tcl_buffer()
        rxPortlist, txPortlist = self._conn.prepare_port_list(
                                    port_lists, rate_percent or 100, latency)
        self._conn.prepare_ixia_for_transmission(txPortlist, rxPortlist)
        # preset port status before running traffic
        self._preset_ixia_port()

    def _start_transmission(self, stream_ids, options={}):
        '''
        :param sample_delay:
        After traffic start ``sample_delay`` seconds, start get runtime statistics
        '''
        # get rate percentage
        rate_percent = options.get('rate') or '100'
        # get duration
        duration = options.get("duration") or 5
        duration = int(duration) if isinstance(duration, (str, unicode)) \
                                      else duration
        # get sample interval
        _sample_delay = options.get("sample_delay") or duration/2
        sample_delay = int(_sample_delay) \
                            if isinstance(_sample_delay, (str, unicode)) \
                            else _sample_delay
        # get configuration from pktgen config file
        warmup = int(self.conf["warmup"]) if self.conf.has_key("warmup") \
                                          else 25
        wait_interval, core_mask = (warmup+30, self.conf["core_mask"]) \
                            if self.conf.has_key("core_mask") \
                            else (warmup+5, None)
        #-------------------------------------------------------------------
        # run ixia server
        try:
            ###########################################
            # Start traffic on port(s)
            self.logger.info("begin traffic ......")
            run_opt = {
                'ports':    self._traffic_ports,
                'mult':     rate_percent,
                'duration': duration,
                'core_mask':core_mask,
                'force':    True,}
            self._conn.start(**run_opt)
        except Exception as e:
            self.logger.error(e)

    def _stop_transmission(self, stream_id):
        # using ixia server command
        if self._traffic_ports:
            self._conn.stop_transmit()

    def _retrieve_port_statistic(self, stream_id, mode):
        ''' ixia traffic statistics '''
        stats = self._conn.get_stats(self._traffic_ports, mode)
        stream = self._get_stream(stream_id)
        self.logger.info(pformat(stream))
        self.logger.info(pformat(stats))
        if mode == 'throughput':
            return self._throughput_stats(stream, stats)
        elif mode == 'loss':
            return self._loss_rate_stats(stream, stats)
        elif mode == 'latency':
            return self._latency_stats(stream, stats)
        else:
            msg = "not support mode <{0}>".format(mode)
            raise Exception(msg)

    def _check_options(self, opts={}):
        # remove it to upper level class and wait for more discussion about
        # pktgen framework
        return True
        for key in opts:
            if key in self.options_keys:
                if key == 'ip':
                    ip = opts['ip']
                    for ip_key in ip:
                        if not ip_key in self.ip_keys:
                            msg = " %s is invalid ip option" % ip_key
                            self.logger.info(msg)
                            return False
                        if key == 'action':
                            if not ip[key] == 'inc' or not ip[key] == 'dec':
                                msg = " %s is invalid ip action" % ip[key]
                                self.logger.info(msg)
                                return False
                elif key == 'vlan':
                    vlan = opts['vlan']
                    for vlan_key in vlan:
                        if not vlan_key in self.vlan_keys:
                            msg = " %s is invalid vlan option" % vlan_key
                            self.logger.info(msg)
                            return False
                        if key == 'action':
                            if not vlan[key] == 'inc' or not ip[key] == 'dec':
                                msg = " %s is invalid vlan action" % vlan[key]
                                self.logger.info(msg)
                                return False
            else:
                msg = " %s is invalid option" % key
                self.logger.info(msg)
                return False
        return True

    def quit_generator(self):
        ''' close ixia session '''
        if self._conn is not None:
            self._disconnect()
        return
