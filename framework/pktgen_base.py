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

import time
import logging
from abc import abstractmethod
from copy import deepcopy
from logger import getLogger
from pprint import pformat

from config import PktgenConf
# packet generator name
from settings import PKTGEN_DPDK, PKTGEN_TREX, PKTGEN_IXIA, PKTGEN

# macro definition
TRANSMIT_CONT = 'continuous'
TRANSMIT_M_BURST = 'multi_burst'
TRANSMIT_S_BURST = 'single_burst'


class PacketGenerator(object):
    """
    Basic class for packet generator, define basic function for each kinds of
    generators
    """
    def __init__(self, tester):
        self.logger = getLogger(PKTGEN)
        self.tester = tester
        self.__streams = []
        self._ports_map = []

    def prepare_generator(self):
        self._prepare_generator()

    def _convert_pktgen_port(self, port_id):
        '''
        :param port_id:
            index of a port in packet generator tool
        '''
        try:
            gen_pci = self._get_port_pci(port_id)
            if not gen_pci:
                msg = "can't get port {0} pci address".format(port_id)
                raise Exception(msg)
            for port_idx, info in enumerate(self.tester.ports_info):
                if 'pci' not in info or info['pci'] == 'N/A':
                    return -1
                tester_pci = info['pci']
                if tester_pci == gen_pci:
                    msg = "gen port {0} map test port {1}".format(
                                                        port_id, port_idx)
                    self.logger.debug(msg)
                    return port_idx
            else:
                port = -1
        except:
            port = -1

        return port

    def _convert_tester_port(self, port_id):
        '''
        :param port_id:
            index of a port in dts tester ports info
        '''
        try:
            info = self.tester.ports_info[port_id]
            # limit to nic port, not including ixia port
            if 'pci' not in info or info['pci'] == 'N/A':
                return -1
            tester_pci = info['pci']
            port = self._get_gen_port(tester_pci)
            msg = "test port {0} map gen port {1}".format(port_id, port)
            self.logger.debug(msg)
        except:
            port = -1

        return port

    def add_stream(self, tx_port, rx_port, pcap_file):
        pktgen_tx_port  = self._convert_tester_port(tx_port)
        pktgen_rx_port  = self._convert_tester_port(rx_port)

        stream_id = len(self.__streams)
        stream = {'tx_port': pktgen_tx_port,
                  'rx_port': pktgen_rx_port,
                  'pcap_file': pcap_file}
        self.__streams.append(stream)

        return stream_id

    def add_streams(self, streams):
        '''' a group of streams '''
        raise NotImplementedError

    def config_stream(self, stream_id=0, opts={}):
        if self._check_options(opts) is not True:
            self.logger.error("Failed to configure stream[%d]" % stream_id)
            return
        stream = self.__streams[stream_id]
        stream['options'] = opts

    def config_streams(self, stream_ids, nic, frame_size, port_num):
        ''' all streams using the default option '''
        raise NotImplementedError

    def get_streams(self):
        return self.__streams

    def clear_streams(self):
        ''' clear streams '''
        self._clear_streams()
        self.__streams = []

    def _set_stream_rate_percent(self, rate_percent):
        ''' set all streams' rate percent '''
        if not self.__streams:
            return
        for stream in self.__streams:
            stream['options']['stream_config']['rate'] = rate_percent

    def _set_stream_pps(self, pps):
        ''' set all streams' pps '''
        if not self.__streams:
            return
        for stream in self.__streams:
            stream['options']['stream_config']['pps'] = pps

    def reset_streams(self):
        self.__streams = []

    def measure_throughput(self, stream_ids=[], options={}):
        """
        Measure throughput on each tx ports
        """
        bps_rx = []
        pps_rx = []
        self._prepare_transmission(stream_ids=stream_ids)
        self._start_transmission(stream_ids, options)

        delay = options.get('delay') or 5
        time.sleep(delay)
        used_rx_port = []
        for stream_id in stream_ids:
            if self.__streams[stream_id]['rx_port'] not in used_rx_port:
                rxbps_rates, rxpps_rates = self._retrieve_port_statistic(
                                                        stream_id, 'throughput')
                used_rx_port.append(self.__streams[stream_id]['rx_port'])
                bps_rx.append(rxbps_rates)
                pps_rx.append(rxpps_rates)
        self._stop_transmission(stream_id)

        bps_rx_total = self._summary_statistic(bps_rx)
        pps_rx_total = self._summary_statistic(pps_rx)
        self.logger.info("throughput: pps_rx %f, bps_rx %f" % (pps_rx_total, bps_rx_total))

        return bps_rx_total, pps_rx_total

    def _measure_loss(self, stream_ids=[], options={}):
        """
        Measure lost rate on each tx/rx ports
        """
        self._prepare_transmission(stream_ids=stream_ids)
        self._start_transmission(stream_ids, options)
        self._stop_transmission(None)
        result = {}
        used_rx_port = []
        for stream_id in stream_ids:
            port_id = self.__streams[stream_id]['rx_port']
            if port_id in used_rx_port:
                continue
            stats = self._retrieve_port_statistic(stream_id, 'loss')
            tx_pkts, rx_pkts = stats
            lost_p = tx_pkts - rx_pkts
            if tx_pkts <= 0:
                loss_rate = 0
            else:
                loss_rate = float(lost_p) / float(tx_pkts)
                if loss_rate < 0:
                    loss_rate = 0
            result[port_id] = (loss_rate, tx_pkts, rx_pkts)
        return result

    def measure_loss(self, stream_ids=[], options={}):
        result = self._measure_loss(stream_ids, options)
        # here only to make sure that return value is the same as dts/etgen format
        # In real testing scenario, this method can offer more data than it
        return result.values()[0]

    def measure_latency(self, stream_ids=[], options={}):
        """
        Measure latency on each tx/rx ports
        """
        self._prepare_transmission(stream_ids=stream_ids, latency=True)
        self._start_transmission(stream_ids, options)
        self._stop_transmission(None)

        result = {}
        used_rx_port = []
        for stream_id in stream_ids:
            port_id = self.__streams[stream_id]['rx_port']
            if port_id in used_rx_port:
                continue
            stats = self._retrieve_port_statistic(stream_id, 'latency')
            result[port_id] = stats
        self.logger.info(result)

        return result

    def _check_loss_rate(self, result, permit_loss_rate):
        '''
        support multiple link peer, if any link peer loss rate happen set
        return value to False
        '''
        for port_id, _result in result.iteritems():
            loss_rate, _, _ = _result
            if loss_rate > permit_loss_rate:
                return False
        else:
            return True

    def measure_rfc2544(self, stream_ids=[], options={}):
        """ check loss rate with rate percent dropping """
        loss_rate_table = []
        rate_percent = options.get('rate') or float(100)
        permit_loss_rate = options.get('pdr') or 0
        self.logger.info("allow loss rate: %f " % permit_loss_rate)
        rate_step = options.get('drop_step') or 1
        result = self._measure_loss(stream_ids, options)
        status = self._check_loss_rate(result, permit_loss_rate)
        loss_rate_table.append([rate_percent, result])
        # if first time loss rate is ok, ignore left flow
        if status:
            # return data is the same with dts/etgen format
            # In fact, multiple link peer have multiple loss rate value,
            # here only pick one
            tx_num, rx_num = result.values()[0][1:]
            return rate_percent, tx_num, rx_num
        _options = deepcopy(options)
        if 'rate' in _options:
            _options.pop('rate')
        while not status and rate_percent > 0:
            rate_percent = rate_percent - rate_step
            if rate_percent <= 0:
                msg = "rfc2544 run under zero rate"
                self.logger.warning(msg)
                break
            self._clear_streams()
            # set stream rate percent to custom value
            self._set_stream_rate_percent(rate_percent)
            # run loss rate testing
            result = self._measure_loss(stream_ids, _options)
            loss_rate_table.append([rate_percent, result])
            status = self._check_loss_rate(result, permit_loss_rate)
        self.logger.info(pformat(loss_rate_table))
        self.logger.info("zero loss rate percent is %f" % rate_percent)
        # use last result as return data to keep the same with dts/etgen format
        # In fact, multiple link peer have multiple loss rate value,
        # here only pick one
        last_result = loss_rate_table[-1]
        rate_percent = last_result[0]
        tx_num, rx_num = last_result[1].values()[0][1:]
        return rate_percent, tx_num, rx_num

    def measure_rfc2544_with_pps(self, stream_ids=[], options={}):
        """
        check loss rate with pps bisecting.(not implemented)

        Currently, ixia/trex use rate percent to control port flow rate,
        pps not supported.
        """
        max_pps = options.get('max_pps')
        min_pps = options.get('min_pps')
        step = options.get('step') or 10000
        permit_loss_rate = options.get('permit_loss_rate') or 0.0001
        # traffic parameters
        loss_pps_table = []
        pps = traffic_pps_max = max_pps
        traffic_pps_min = min_pps

        while True:
            # set stream rate percent to custom value
            self._set_stream_pps(pps)
            # run loss rate testing
            _options = deepcopy(options)
            result = self._measure_loss(stream_ids, _options)
            loss_pps_table.append([pps, result])
            status = self._check_loss_rate(result, permit_loss_rate)
            if status:
                traffic_pps_max = pps
            else:
                traffic_pps_min = pps
            if traffic_pps_max - traffic_pps_min < step:
                break
            pps = (traffic_pps_max - traffic_pps_min)/2 + traffic_pps_min

        self.logger.info("zero loss pps is %f" % last_no_lost_mult)
        # use last result as return data to keep the same with dts/etgen format
        # In fact, multiple link peer have multiple loss rate value,
        # here only pick one
        return loss_pps_table[-1][1].values()[0]

    def measure(self, stream_ids, traffic_opt):
        '''
        use as an unify interface method for packet generator
        '''
        method = traffic_opt.get('method')
        if method == 'throughput':
            result = self.measure_throughput(stream_ids, traffic_opt)
        elif method == 'latency':
            result = self.measure_latency(stream_ids, traffic_opt)
        elif method == 'loss':
            result = self.measure_loss(stream_ids, traffic_opt)
        elif method == 'rfc2544':
            result = self.measure_rfc2544(stream_ids, traffic_opt)
        elif method == 'rfc2544_with_pps':
            result = self.measure_rfc2544_with_pps(stream_ids, traffic_opt)
        else:
            result = None

        return result

    def _summary_statistic(self, array=[]):
        """
        Summary all values in statistic array
        """
        summary = 0.000
        for value in array:
            summary += value

        return summary

    def _get_stream(self, stream_id):
        return self.__streams[stream_id]

    def _get_generator_conf_instance(self):
        conf_inst = PktgenConf(self.pktgen_type)
        pktgen_inst_type = conf_inst.pktgen_conf.get_sections()
        if len(pktgen_inst_type) < 1:
            msg = ("packet generator <{0}> has no configuration "
                   "in pktgen.cfg").format(self.pktgen_type)
            raise Exception(msg)
        return conf_inst

    @abstractmethod
    def _prepare_transmission(self, stream_ids=[], latency=False):
        pass

    @abstractmethod
    def _start_transmission(self, stream_ids, options={}):
        pass

    @abstractmethod
    def _stop_transmission(self, stream_id):
        pass

    @abstractmethod
    def _retrieve_port_statistic(self, stream_id, mode):
        pass

    @abstractmethod
    def _check_options(self, opts={}):
        pass

    @abstractmethod
    def quit_generator(self):
        pass


class DpdkPacketGenerator(PacketGenerator): pass # not implemented