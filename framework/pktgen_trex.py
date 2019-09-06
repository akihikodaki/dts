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
import sys
import time
import logging
from pprint import pformat

from pktgen_base import (PacketGenerator, PKTGEN_TREX,
                         TRANSMIT_CONT, TRANSMIT_M_BURST, TRANSMIT_S_BURST)

FORMAT = '%(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(os.path.basename(__file__)[:-3].upper())
logger.setLevel(logging.INFO)


class TrexConfigVm(object):
    '''
    config one stream vm format of trex
    '''
    def __init__(self):
        from trex_stl_lib.api import (ipv4_str_to_num, mac2str, is_valid_ipv4_ret)
        self.ipv4_str_to_num = ipv4_str_to_num
        self.is_valid_ipv4_ret = is_valid_ipv4_ret
        self.mac2str = mac2str

    def _mac_var(self, fv_name, mac_start, mac_end, step, mode):
        '''
        create mac address vm format of trex
        '''
        _mac_start = self.ipv4_str_to_num(self.mac2str(mac_start)[2:])
        _mac_end = self.ipv4_str_to_num(self.mac2str(mac_end)[2:])
        if mode == 'inc' or mode == 'dec':
            min_value = _mac_start
            max_value = _mac_end
        elif mode == 'random':
            max_value = 0xffffffff
            min_value = 0
        add_val = 0

        var = [{
            'name': fv_name,
            'min_value': min_value,
            'max_value': max_value,
            'size': 4,
            'step': step,
            'op': mode,},
            {'write': {'add_val': add_val, 'offset_fixup': 2}}]

        return var

    def _ip_vm_var(self, fv_name, ip_start, ip_end, step, mode):
        '''
        create ip address vm format of trex
        '''
        _ip_start = self.ipv4_str_to_num(self.is_valid_ipv4_ret(ip_start))
        _ip_end = self.ipv4_str_to_num(self.is_valid_ipv4_ret(ip_end))
        _step = self.ipv4_str_to_num(self.is_valid_ipv4_ret(step)) \
                                if isinstance(step, (str, unicode)) else step
        if mode == 'inc' or mode == 'dec':
            min_value = _ip_start
            max_value = _ip_end
        elif mode == 'random':
            max_value = 0xffffffff
            min_value = 0
        add_val = 0

        var = [{
            'name': fv_name,
            'min_value': min_value,
            'max_value': max_value,
            'size': 4,
            'step': _step,
            'op': mode,},
            {'write': {'add_val': add_val},
             'fix_chksum': {}}]

        return var

    def config_trex_vm(self, option):
        '''
        config one stream vm
        '''
        vm_var = {}
        ###################################################################
        # mac inc/dec/random
        if 'mac' in option:
            for name, config in option['mac'].iteritems():
                mac_start = config.get('start') or '00:00:00:00:00:00'
                mac_end = config.get('end') or 'FF:FF:FF:FF:FF:FF'
                step = config.get('step') or 1
                mode = config.get('action') or 'inc'
                #-----------------
                fv_name = 'Ethernet.{0}'.format(name)
                # layer/field name
                vm_var[fv_name] = self._mac_var(fv_name,
                                            mac_start, mac_end,
                                            step, mode)
        ###################################################################
        # src ip mask inc/dec/random
        if 'ip' in option:
            for name, config in option['ip'].iteritems():
                ip_start = config.get('start') or '0.0.0.1'
                ip_end = config.get('end') or '0.0.0.255'
                step = config.get('step') or 1
                mode = config.get('action') or 'inc'
                #-----------------
                fv_name = 'IP.{0}'.format(name)
                # layer/field name
                vm_var[fv_name] = self._ip_vm_var(fv_name, ip_start, ip_end,
                                                 step, mode)
        ###################################################################
        #  merge var1/var2/random/cache into one method
        ###################################################################
        # src ip mask inc/dec/random
        if 'port' in option:
            for name, config in option['port'].iteritems():
                protocol = config.get('protocol') or 'UDP'
                port_start = config.get('start') or 1
                port_end = config.get('end') or 255
                step = config.get('step') or 1
                mode = config.get('action') or 'inc'
                #-----------------
                fv_name = '{0}.{1}'.format(protocol.upper(), name)
                # layer/field name
                vm_var[fv_name] = {
                    'name': fv_name,
                    'min_value': port_start,
                    'max_value': port_end,
                    'size': 2,
                    'step': step,
                    'op': mode,}
        ###################################################################
        # vlan field inc/dec/random
        if 'vlan' in option:
            for name, config in option['vlan'].iteritems():
                vlan_start = config.get('start') \
                                if config.get('start') != None else 0
                vlan_end = config.get('end') or 256
                step = config.get('step') or 1
                mode = config.get('action') or 'inc'
                #-----------------
                fv_name = '802|1Q:{0}.vlan'.format(name)
                # vlan layer/field name
                vm_var[fv_name] = {
                    'name': fv_name,
                    'min_value': vlan_start,
                    'max_value': vlan_end,
                    'size': 2,
                    'step': step,
                    'op': mode,}
        ###################################################################
        # payload change with custom sizes
        if 'pkt_size' in option:
            # note:
            # when using mixed stream, which have different sizes
            # this will be forbidden
            step = 1
            mode = 'random'
            min_pkt_size = option['pkt_size']['start']
            max_pkt_size = option['pkt_size']['end']
            #-----------------
            l3_len_fix = -len(Ether())
            l4_len_fix = l3_len_fix - len(IP())

            var = {
                'name': 'fv_rand',
                # src ip increase with a range
                'min_value': min_pkt_size - 4,
                'max_value': max_pkt_size - 4,
                'size': 2,
                'step': step,
                'op': mode,}

            vm_var = {
            'IP.len': [
                var, {'write': {'add_val': l3_len_fix},
                      'trim': {},
                      'fix_chksum': {}}],
            'UDP.len': [
                var, {'write': {'add_val': l4_len_fix},
                      'trim': {},
                      'fix_chksum': {}}]}

        return vm_var


class TrexConfigStream(object):

    def __init__(self):
        from trex_stl_lib.api import (
                    STLTXCont, STLTXSingleBurst, STLTXMultiBurst,
                    STLPktBuilder, STLProfile, STLVM,
                    STLStream, STLStreamDstMAC_PKT,
                    STLFlowLatencyStats)

        # set trex class
        self.STLStream = STLStream
        self.STLPktBuilder = STLPktBuilder
        self.STLProfile = STLProfile
        self.STLVM = STLVM
        self.STLTXCont = STLTXCont
        self.STLTXSingleBurst = STLTXSingleBurst
        self.STLTXMultiBurst = STLTXMultiBurst
        self.STLFlowLatencyStats = STLFlowLatencyStats
        self.STLStreamDstMAC_PKT = STLStreamDstMAC_PKT

    def _set_var_default_value(self, config):
        default = {
            'init_value': None,
            'min_value': 0,
            'max_value': 255,
            'size': 4,
            'step': 1}
        for name, value in default.iteritems():
            if name not in config:
                config[name] = value

    def _preset_layers(self, vm_var, configs):
        '''
        configure stream behavior on pcap format
        '''
        msg = "layer <{0}> field name <{1}> is not defined".format
        fv_names = []
        fix_chksum = False
        for layer, _config in configs.iteritems():
            # set default value
            if isinstance(_config, (tuple, list)):
                config = _config[0]
                op_config = _config[1]
            else:
                config = _config
                op_config = None

            name = config.get('name')
            if not name:
                error = msg(layer, name)
                raise Exception(error)

            self._set_var_default_value(config)
            # different fields with a range (relevance variables)
            if isinstance(layer, (tuple, list)):
                vm_var.tuple_var(**config)
                for offset in layer:
                    fv_name = name+'.ip' if offset.startswith('IP') else \
                              name+'.port'
                    _vars = {'fv_name': fv_name, 'pkt_offset': offset}
                    if op_config and 'write' in op_config:
                        _vars.update(op_config['write'])

                    if fv_name not in fv_names:
                        fv_names.append(fv_name)
                        vm_var.write(**_vars)
            # different fields with a range (independent variable)
            else:
                if name not in fv_names:
                    fv_names.append(name)
                    vm_var.var(**config)
                # write behavior in field
                _vars = {'fv_name': name, 'pkt_offset': layer}
                if op_config and 'write' in op_config:
                    _vars.update(op_config['write'])
                vm_var.write(**_vars)

            # Trim the packet size by the stream variable size
            if op_config and 'trim' in op_config:
                vm_var.trim(name)
            # set VM as cached with a cache size
            if op_config and 'set_cached' in op_config:
                vm_var.set_cached(op_config['set_cached'])
            # Fix IPv4 header checksum
            if op_config and 'fix_chksum' in op_config:
                fix_chksum = True

        # protocol type
        if fix_chksum:
            vm_var.fix_chksum()

    def _create_stream(self, _pkt, stream_opt, vm=None, flow_stats=None):
        '''
        create trex stream
        '''
        isg = stream_opt.get('isg') or 0.5
        mode = stream_opt.get('transmit_mode') or TRANSMIT_CONT
        txmode_opt = stream_opt.get('txmode') or {}
        pps = txmode_opt.get('pps')
        # Continuous mode
        if mode == TRANSMIT_CONT:
            mode_inst = self.STLTXCont(pps=pps)
        # Single burst mode
        elif mode == TRANSMIT_S_BURST:
            total_pkts = txmode_opt.get('total_pkts') or 32
            mode_inst = self.STLTXSingleBurst(pps=pps, total_pkts=total_pkts)
        # Multi-burst mode
        elif mode == TRANSMIT_M_BURST:
            burst_pkts = txmode_opt.get('burst_pkts') or 32
            bursts_count = txmode_opt.get('bursts_count') or 2
            ibg = txmode_opt.get('ibg') or 10
            mode_inst = self.STLTXMultiBurst(pkts_per_burst = burst_pkts,
                                        count = bursts_count,
                                        ibg = ibg)
        else:
            msg = 'not support format {0}'.format(mode)
            raise Exception(msg)

        pkt = self.STLPktBuilder(pkt=_pkt, vm=vm)
        _stream = self.STLStream(
            packet=pkt, mode=mode_inst, isg=isg,
            flow_stats=flow_stats,
            mac_dst_override_mode=self.STLStreamDstMAC_PKT)

        return _stream

    def _generate_vm(self, vm_conf):
        '''
        create packet fields trex vm instance
        '''
        if not vm_conf:
            return None
        # config packet vm format for trex
        hVmConfig = TrexConfigVm()
        _vm_var = hVmConfig.config_trex_vm(vm_conf)
        if not isinstance(_vm_var, self.STLVM):
            vm_var = self.STLVM()
            self._preset_layers(vm_var, _vm_var)
        else:
            vm_var = _vm_var

        return vm_var

    def _get_streams(self, streams_config):
        '''
        create a group of streams
        '''
        # vm_var is the instance to config pcap fields
        # create a group of streams, which are using different size payload
        streams = []

        for config in streams_config:
            _pkt = config.get('pcap')
            vm_conf = config.get('fields_config')
            _stream_op = config.get('stream_config')
            # configure trex vm
            vm_var = self._generate_vm(vm_conf)
            # create
            streams.append(self._create_stream( _pkt, _stream_op, vm_var))
        _streams = self.STLProfile(streams).get_streams()

        return _streams

    def add_streams(self, conn, streams_config, ports=None, latency=False):
        '''
        create one/multiple of streams on one port of trex server
        '''
        # normal streams configuration
        _streams = self._get_streams(streams_config)
        # create latency statistics stream
        # use first one of main stream config as latency statistics stream
        if latency:
            streams = list(_streams)
            flow_stats = self.STLFlowLatencyStats(pg_id=ports[0])
            latency_opt = streams_config[0]
            _pkt = latency_opt.get('pcap')
            _stream_op = latency_opt.get('stream_config')
            _stream = self._create_stream( _pkt, _stream_op,
                                           flow_stats=flow_stats)
            streams.append(_stream)
        else:
            streams = _streams

        conn.add_streams(streams, ports=ports)


class TrexPacketGenerator(PacketGenerator):
    """
    Trex packet generator, detail usage can be seen at
    https://trex-tgn.cisco.com/trex/doc/trex_manual.html
    """
    def __init__(self, tester):
        self.pktgen_type = PKTGEN_TREX
        self.trex_app = "t-rex-64"
        self._conn = None
        self.control_session = None
        # trex management
        self._traffic_opt = {}
        self._ports = []
        self._traffic_ports = []
        self._rx_ports = []
        self.runtime_stats = {}

        conf_inst = self._get_generator_conf_instance()
        self.conf = conf_inst.load_pktgen_config()

        self.options_keys = [
            'txmode', 'ip', 'vlan', 'transmit_mode', 'rate']
        self.ip_keys = ['start', 'end','action', 'mask', 'step']
        self.vlan_keys = ['start', 'end', 'action', 'step', 'count']

        super(TrexPacketGenerator, self).__init__(tester)

        # check trex binary file
        trex_bin = os.sep.join([self.conf.get('trex_root_path'), self.trex_app])
        if not os.path.exists(trex_bin):
            msg = "{0} is not existed, please check {1} content".format(
                                    trex_bin, conf_inst.config_file)
            raise Exception(msg)
        # if `trex_lib_path` is not set, use a default relative directory.
        trex_lib_dir = \
                self.conf.get('trex_lib_path') \
                                if self.conf.get('trex_lib_path') else \
                "{0}/automation/trex_control_plane/stl".format(
                                            self.conf.get('trex_root_path'))
        # check trex lib root directory
        if not os.path.exists(trex_lib_dir):
            msg = ("{0} is not existed, please check {1} content and "
                   "set `trex_lib_path`").format(trex_lib_dir, conf_inst.config_file)
            raise Exception(msg)
        # check if trex lib is existed
        trex_lib = os.sep.join([trex_lib_dir, 'trex_stl_lib'])
        if not os.path.exists(trex_lib):
            msg = "no 'trex_stl_lib' package under {0}".format(trex_lib_dir)
            raise Exception(msg)
        # import t-rex libs
        sys.path.insert(0, trex_lib_dir)
        from trex_stl_lib.api import STLClient
        # set trex class
        self.STLClient = STLClient

    def _connect(self):
        self._conn = self.STLClient(server=self.conf["server"])
        self._conn.connect()
        for p in self._conn.get_all_ports():
            self._ports.append(p)

        self.logger.debug(self._ports)

    def _get_port_pci(self, port_id):
        '''
        get port pci address
        '''
        for name, _port_obj in self._conn.ports.iteritems():
            if name == port_id:
                _pci = _port_obj.info['pci_addr']
                return _pci
        else:
            return None

    def _get_gen_port(self, pci):
        '''
        get port management id of the packet generator
        '''
        for name, _port_obj in self._conn.ports.iteritems():
            _pci = _port_obj.info['pci_addr']
            if _pci == pci:
                return name
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

    def get_ports(self):
        """
        Return self ports information
        """
        ports = []
        for idx in range(len(self._ports)):
            port_info = self._conn.ports[idx]
            pci = port_info.info['pci_addr']
            mac = port_info.info['hw_mac']
            ports.append({
                'intf': 'TREX:%d' % idx,
                'mac': mac,
                'pci': pci,
                'type': 'trex',})
        return ports

    def _clear_streams(self):
        ''' clear streams in trex and `PacketGenerator` '''
        # if streams has been attached, remove them from trex server.
        self._remove_all_streams()

    def _remove_all_streams(self):
        ''' remove all stream deployed on trex port(s) '''
        if not self.get_streams():
            return
        if not self._conn.get_acquired_ports():
            return
        self._conn.remove_all_streams()

    def _disconnect(self):
        ''' disconnect with trex server '''
        try:
            self._remove_all_streams()
            self._conn.disconnect()
        except Exception as e:
            msg = 'Error disconnecting: %s' % e
            self.logger.error(msg)
        self._conn = None

    def _check_options(self, opts={}):
        return True # close it and wait for more discussion about pktgen framework
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

    def _prepare_generator(self):
        ''' start trex server '''
        if self.conf.has_key('start_trex') and self.conf['start_trex']:
            app_param_temp = "-i"
            # flow control
            flow_control = self.conf.get('flow_control')
            flow_control_opt = '--no-flow-control-change' if flow_control else ''

            for key in self.conf:
                #key, value = pktgen_conf
                if key == 'config_file':
                    app_param_temp = app_param_temp + " --cfg " + self.conf[key]
                elif key == 'core_num':
                    app_param_temp = app_param_temp + " -c " + self.conf[key]
            self.control_session = \
                        self.tester.create_session('trex_control_session')

            self.control_session.send_expect(
               ';'.join(['cd ' + self.conf['trex_root_path'],
                './' + self.trex_app + " " + app_param_temp]),
                                        '-Per port stats table', 30)
        try:
            self._connect()
        except Exception as e:
            msg = "failed to connect to t-rex server"
            raise Exception(msg)

    @property
    def _vm_conf(self):
        return None # close it and wait for more discussion about pktgen framework
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

        if conf:
            return conf
        else:
            return None

    def _get_port_features(self, port_id):
        ''' get ports' features '''
        ports = self._conn.ports
        if port_id not in ports:
            return None
        features = self._conn.ports[port_id].get_formatted_info()
        self.logger.info(pformat(features))

        return features

    def _is_support_flow_control(self, port_id):
        ''' check if a port support flow control '''
        features = self._get_port_features(port_id)
        if not features or features.get('fc_supported') == 'no':
            msg = "trex port <{0}> not support flow control".format(port_id)
            self.logger.warning(msg)
            return False
        else:
            return True

    def _preset_trex_port(self):
        ''' set ports promiscuous/flow_ctrl attribute '''
        rx_ports = self._rx_ports
        # for trex design requirement, all ports of trex should be the same type
        # nic, here use first port to check flow control attribute
        flow_ctrl = self._traffic_opt.get('flow_control') \
                        if self._is_support_flow_control(rx_ports[0]) else None
        flow_ctrl_flag = flow_ctrl.get('flag') or 1 if flow_ctrl else None
        # flow control of port running trex traffic
        self._conn.set_port_attr( rx_ports,
                                  promiscuous=True,
                                  link_up=True,
                                  flow_ctrl = flow_ctrl_flag)

    def _throughput_stats(self, stream, stats):
        # tx packet
        tx_port_id = stream["tx_port"]
        port_stats = self.runtime_stats.get(tx_port_id)
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
        port_stats = self.runtime_stats.get(rx_port_id)
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
        _stats = stats.get('latency')
        port_id = stream.get("tx_port")
        if port_id in _stats.keys():
            port_stats = _stats[port_id]['latency']
        else:
            msg = "port {0} latency stats is not found".format(port_id)
            self.logger.error(msg)
            return None

        latency_stats = {
            'min':    port_stats.get('total_min'),
            'max':    port_stats.get('total_max'),
            'average':port_stats.get('average'),}

        return latency_stats

    def _prepare_transmission(self, stream_ids=[], latency=False):
        ''' add one/multiple streams in one/multiple ports '''
        port_config = {}
        for stream_id in stream_ids:
            stream = self._get_stream(stream_id)
            tx_port = stream['tx_port']
            rx_port = stream['rx_port']
            # save port id list
            if tx_port not in self._traffic_ports:
                self._traffic_ports.append(tx_port)
            if rx_port not in self._rx_ports:
                self._rx_ports.append(rx_port)
            # set all streams in one port to do batch configuration
            options = stream['options']
            if tx_port not in port_config.keys():
                port_config[tx_port] = []
            config = {}
            config.update(options)
            # since trex stream rate percent haven't taken effect, here use one
            # stream rate percent as port rate percent. In pktgen, all streams
            # rate percent are the same value by design. flow control option is
            # the same.
            stream_config = options.get('stream_config') or {}
            self._traffic_opt['rate'] = stream_config.get('rate') or 100
            if stream_config.get('pps'): # reserve feature
                self._traffic_opt['pps'] = stream_config.get('pps')
            # flow control option is deployed on all ports by design
            self._traffic_opt['flow_control'] = options.get('flow_control') or {}
            # if vm config by pktgen config file, set it here to take the place
            # of user setting
            if self._vm_conf:
                config['fields_config'] = self._vm_conf
            port_config[tx_port].append(config)

        if not port_config:
            msg = 'no stream options for trex packet generator'
            raise Exception(msg)

        self._conn.reset(ports=self._ports)
        config_inst = TrexConfigStream()
        for port_id, config in port_config.iteritems():
            # add a group of streams in one port
            config_inst.add_streams(self._conn, config, ports=[port_id],
                                    latency=latency)
        # preset port status before running traffic
        self._preset_trex_port()

    def _start_transmission(self, stream_ids, options={}):
        '''
        :param sample_delay:
        After traffic start ``sample_delay`` seconds, start get runtime statistics
        '''
        # get rate percentage
        rate_percent = "{0}%".format(options.get('rate') or
                                     self._traffic_opt.get('rate') or
                                     '100')
        # get duration
        duration = options.get("duration") or 20
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
        # set trex coremask
        wait_interval, core_mask = (
                        warmup+30, int(self.conf["core_mask"], 16)) \
                            if self.conf.has_key("core_mask") \
                            else (warmup+5, 0x3)

        try:
            ###########################################
            # clear the stats before injecting
            self._conn.clear_stats()
            # Start traffic on port(s)
            run_opt = {
                'ports':    self._traffic_ports,
                'mult':     rate_percent,
                'duration': duration,
                'core_mask':core_mask,
                'force':    True,}
            self.logger.info("begin traffic ......")
            self._conn.start(**run_opt)
            ###########################################
            if sample_delay:
                time.sleep(sample_delay) # wait
                # get ports runtime statistics
                self.runtime_stats = self._conn.get_stats()
                self.logger.info(pformat(self.runtime_stats))
            ###########################################
            # Block until traffic on specified port(s) has ended
            wait_opt = {'ports':  self._traffic_ports}
            if duration:
                time.sleep(wait_interval + 10)
                wait_opt['timeout'] = wait_interval + duration
            self._conn.wait_on_traffic(**wait_opt)
        except Exception as e:
            self.logger.error(e)

    def _stop_transmission(self, stream_id):
        if self._traffic_ports:
            self._conn.stop(ports=self._traffic_ports, rx_delay_ms=5000)

    def _retrieve_port_statistic(self, stream_id, mode):
        '''
        trex traffic statistics
        '''
        stats = self._conn.get_stats()
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
            return None

    def quit_generator(self):
        if self._conn is not None:
            self._disconnect()
        if self.control_session is not None:
            self.tester.send_expect('pkill -f _t-rex-64', '# ')
            time.sleep(5)
            self.tester.destroy_session(self.control_session)
            self.control_session = None
