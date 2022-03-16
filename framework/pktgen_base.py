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

import logging
import time
from abc import abstractmethod
from copy import deepcopy
from enum import Enum, unique
from pprint import pformat

from .config import PktgenConf
from .logger import getLogger

# packet generator name
from .settings import PKTGEN, PKTGEN_DPDK, PKTGEN_IXIA, PKTGEN_IXIA_NETWORK, PKTGEN_TREX

# macro definition
TRANSMIT_CONT = "continuous"
TRANSMIT_M_BURST = "multi_burst"
TRANSMIT_S_BURST = "single_burst"


@unique
class STAT_TYPE(Enum):
    RX = "rx"
    TXRX = "txrx"


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
        self.pktgen_type = None

    def _prepare_generator(self):
        raise NotImplementedError

    def prepare_generator(self):
        self._prepare_generator()

    def _get_port_pci(self, port_id):
        raise NotImplementedError

    def _convert_pktgen_port(self, port_id):
        """
        :param port_id:
            index of a port in packet generator tool
        """
        try:
            gen_pci = self._get_port_pci(port_id)
            if not gen_pci:
                msg = "can't get port {0} pci address".format(port_id)
                raise Exception(msg)
            for port_idx, info in enumerate(self.tester.ports_info):
                if "pci" not in info or info["pci"] == "N/A":
                    return -1
                tester_pci = info["pci"]
                if tester_pci == gen_pci:
                    msg = "gen port {0} map test port {1}".format(port_id, port_idx)
                    self.logger.debug(msg)
                    return port_idx
            else:
                port = -1
        except Exception as e:
            port = -1

        return port

    def _get_gen_port(self, tester_pci):
        raise NotImplementedError

    def _convert_tester_port(self, port_id):
        """
        :param port_id:
            index of a port in dts tester ports info
        """
        try:
            info = self.tester.ports_info[port_id]
            # limit to nic port, not including ixia port
            if "pci" not in info or info["pci"] == "N/A":
                return -1
            tester_pci = info["pci"]
            port = self._get_gen_port(tester_pci)
            msg = "test port {0} map gen port {1}".format(port_id, port)
            self.logger.debug(msg)
        except Exception as e:
            port = -1

        return port

    def add_stream(self, tx_port, rx_port, pcap_file):
        pktgen_tx_port = self._convert_tester_port(tx_port)
        pktgen_rx_port = self._convert_tester_port(rx_port)

        stream_id = len(self.__streams)
        stream = {
            "tx_port": pktgen_tx_port,
            "rx_port": pktgen_rx_port,
            "pcap_file": pcap_file,
        }
        self.__streams.append(stream)

        return stream_id

    def add_streams(self, streams):
        """' a group of streams"""
        raise NotImplementedError

    def config_stream(self, stream_id=0, opts={}):
        if self._check_options(opts) is not True:
            self.logger.error("Failed to configure stream[%d]" % stream_id)
            return
        stream = self.__streams[stream_id]
        stream["options"] = opts

    def config_streams(self, stream_ids, nic, frame_size, port_num):
        """all streams using the default option"""
        raise NotImplementedError

    def get_streams(self):
        return self.__streams

    def _clear_streams(self):
        raise NotImplementedError

    def clear_streams(self):
        """clear streams"""
        self._clear_streams()
        self.__streams = []

    def _set_stream_rate_percent(self, rate_percent):
        """set all streams' rate percent"""
        if not self.__streams:
            return
        for stream in self.__streams:
            stream["options"]["stream_config"]["rate"] = rate_percent

    def _set_stream_pps(self, pps):
        """set all streams' pps"""
        if not self.__streams:
            return
        for stream in self.__streams:
            stream["options"]["stream_config"]["pps"] = pps

    def reset_streams(self):
        self.__streams = []

    def __warm_up_pktgen(self, stream_ids, options, delay):
        """run warm up traffic before start main traffic"""
        if not delay:
            return
        msg = "{1} packet generator: run traffic {0}s to warm up ... ".format(
            delay, self.pktgen_type
        )
        self.logger.info(msg)
        self._start_transmission(stream_ids, options)
        time.sleep(delay)
        self._stop_transmission(stream_ids)

    def __get_single_throughput_statistic(self, stream_ids, stat_type=None):
        bps_rx = []
        pps_rx = []
        bps_tx = []
        pps_tx = []
        used_rx_port = []
        msg = "begin get port statistic ..."
        self.logger.info(msg)
        for stream_id in stream_ids:
            if self.__streams[stream_id]["rx_port"] not in used_rx_port:
                bps_rate, pps_rate = self._retrieve_port_statistic(
                    stream_id, "throughput"
                )
                used_rx_port.append(self.__streams[stream_id]["rx_port"])
                if stat_type and stat_type is STAT_TYPE.TXRX:
                    bps_tx.append(bps_rate[0])
                    pps_tx.append(pps_rate[0])

                if isinstance(bps_rate, tuple) and isinstance(pps_rate, tuple):
                    bps_rx.append(bps_rate[1])
                    pps_rx.append(pps_rate[1])
                else:
                    bps_rx.append(bps_rate)
                    pps_rx.append(pps_rate)
        if stat_type and stat_type is STAT_TYPE.TXRX:
            bps_tx_total = self._summary_statistic(bps_tx)
            pps_tx_total = self._summary_statistic(pps_tx)
            bps_rx_total = self._summary_statistic(bps_rx)
            pps_rx_total = self._summary_statistic(pps_rx)
            self.logger.info(
                "throughput: pps_tx %f, bps_tx %f" % (pps_tx_total, bps_tx_total)
            )
            self.logger.info(
                "throughput: pps_rx %f, bps_rx %f" % (pps_rx_total, bps_rx_total)
            )

            return (bps_tx_total, bps_rx_total), (pps_tx_total, pps_rx_total)
        else:
            bps_rx_total = self._summary_statistic(bps_rx)
            pps_rx_total = self._summary_statistic(pps_rx)
            self.logger.info(
                "throughput: pps_rx %f, bps_rx %f" % (pps_rx_total, bps_rx_total)
            )

            return bps_rx_total, pps_rx_total

    def __get_multi_throughput_statistic(
        self, stream_ids, duration, interval, callback=None, stat_type=None
    ):
        """
        duration: traffic duration (second)
        interval: interval of get throughput statistics (second)
        callback: a callback method of suite, which is used to do some actions
            during traffic lasting.

        Return: a list of throughput instead of a single tuple of pps/bps rate
        """
        time_elapsed = 0
        stats = []
        while time_elapsed < duration:
            time.sleep(interval)
            stats.append(self.__get_single_throughput_statistic(stream_ids, stat_type))
            if callback and callable(callback):
                callback()
            time_elapsed += interval
        return stats

    def measure_throughput(self, stream_ids=[], options={}):
        """
        Measure throughput on each tx ports

        options usage:
            rate:
                port rate percent, float(0--100). Default value is 100.

            delay:
                warm up time before start main traffic. If it is set, it will start
                a delay time traffic to make sure packet generator under good status.
                Warm up flow is ignored by default.

            interval:
                a interval time of get throughput statistic (second)
                If set this key value, pktgen will return several throughput statistic
                data within a duration traffic. If not set this key value, only
                return one statistic data. It is ignored by default.

            callback:
                this key works with ``interval`` key. If it is set, the callback
                of suite level will be executed after getting throughput statistic.
                callback method should define as below, don't add sleep in this method.

                def callback(self):
                    xxxx()

            duration:
                traffic lasting time(second). Default value is 10 second.

            stat_type(for trex only):
                STAT_TYPE.RX  return (rx bps, rx_pps)
                STAT_TYPE.TXRX return ((tx bps, rx_bps), (tx pps, rx_pps))
        """
        interval = options.get("interval")
        callback = options.get("callback")
        duration = options.get("duration") or 10
        delay = options.get("delay")
        if self.pktgen_type == PKTGEN_TREX:
            stat_type = options.get("stat_type") or STAT_TYPE.RX
        else:
            if options.get("stat_type") is not None:
                msg = (
                    "'stat_type' option is only for trex, "
                    "should not set when use other pktgen tools"
                )
                raise Exception(msg)
            stat_type = STAT_TYPE.RX
        self._prepare_transmission(stream_ids=stream_ids)
        # start warm up traffic
        self.__warm_up_pktgen(stream_ids, options, delay)
        # main traffic
        self._start_transmission(stream_ids, options)
        # keep traffic within a duration time and get throughput statistic
        if interval and duration:
            stats = self.__get_multi_throughput_statistic(
                stream_ids, duration, interval, callback, stat_type
            )
        else:
            time.sleep(duration)
            stats = self.__get_single_throughput_statistic(stream_ids, stat_type)
        self._stop_transmission(stream_ids)
        return stats

    def _measure_loss(self, stream_ids=[], options={}):
        """
        Measure lost rate on each tx/rx ports
        """
        delay = options.get("delay")
        duration = options.get("duration") or 10
        throughput_stat_flag = options.get("throughput_stat_flag") or False
        self._prepare_transmission(stream_ids=stream_ids)
        # start warm up traffic
        self.__warm_up_pktgen(stream_ids, options, delay)
        # main traffic
        self._start_transmission(stream_ids, options)
        # keep traffic within a duration time
        time.sleep(duration)
        if throughput_stat_flag:
            _throughput_stats = self.__get_single_throughput_statistic(stream_ids)
        self._stop_transmission(None)
        result = {}
        used_rx_port = []
        for stream_id in stream_ids:
            port_id = self.__streams[stream_id]["rx_port"]
            if port_id in used_rx_port:
                continue
            stats = self._retrieve_port_statistic(stream_id, "loss")
            tx_pkts, rx_pkts = stats
            lost_p = tx_pkts - rx_pkts
            if tx_pkts <= 0:
                loss_rate = 0
            else:
                loss_rate = float(lost_p) / float(tx_pkts)
                if loss_rate < 0:
                    loss_rate = 0
            result[port_id] = (loss_rate, tx_pkts, rx_pkts)
        if throughput_stat_flag:
            return result, _throughput_stats
        else:
            return result

    def measure_loss(self, stream_ids=[], options={}):
        """
        options usage:
            rate:
                port rate percent, float(0--100). Default value is 100.

            delay:
                warm up time before start main traffic. If it is set, it will
                start a delay time traffic to make sure packet generator
                under good status. Warm up flow is ignored by default.

            duration:
                traffic lasting time(second). Default value is 10 second.
        """
        result = self._measure_loss(stream_ids, options)
        # here only to make sure that return value is the same as dts/etgen format
        # In real testing scenario, this method can offer more data than it
        return list(result.values())[0]

    def _measure_rfc2544_ixnet(self, stream_ids=[], options={}):
        """
        used for ixNetwork
        """
        # main traffic
        self._prepare_transmission(stream_ids=stream_ids)
        self._start_transmission(stream_ids, options)
        self._stop_transmission(None)
        # parsing test result
        stats = self._retrieve_port_statistic(stream_ids[0], "rfc2544")
        tx_pkts, rx_pkts, pps = stats
        lost_p = tx_pkts - rx_pkts
        if tx_pkts <= 0:
            loss_rate = 0
        else:
            loss_rate = float(lost_p) / float(tx_pkts)
            if loss_rate < 0:
                loss_rate = 0
        result = (loss_rate, tx_pkts, rx_pkts, pps)
        return result

    def measure_latency(self, stream_ids=[], options={}):
        """
        Measure latency on each tx/rx ports

        options usage:
            rate:
                port rate percent, float(0--100). Default value is 100.

            delay:
                warm up time before start main traffic. If it is set, it will
                start a delay time transmission to make sure packet generator
                under correct status. Warm up flow is ignored by default.

            duration:
                traffic lasting time(second). Default value is 10 second.
        """
        delay = options.get("delay")
        duration = options.get("duration") or 10
        self._prepare_transmission(stream_ids=stream_ids, latency=True)
        # start warm up traffic
        self.__warm_up_pktgen(stream_ids, options, delay)
        # main traffic
        self._start_transmission(stream_ids, options)
        # keep traffic within a duration time
        time.sleep(duration)
        self._stop_transmission(None)

        result = {}
        used_rx_port = []
        for stream_id in stream_ids:
            port_id = self.__streams[stream_id]["rx_port"]
            if port_id in used_rx_port:
                continue
            stats = self._retrieve_port_statistic(stream_id, "latency")
            result[port_id] = stats
        self.logger.info(result)

        return result

    def _check_loss_rate(self, result, permit_loss_rate):
        """
        support multiple link peer, if any link peer loss rate happen set
        return value to False
        """
        for port_id, _result in result.items():
            loss_rate, _, _ = _result
            if loss_rate > permit_loss_rate:
                return False
        else:
            return True

    def measure_rfc2544(self, stream_ids=[], options={}):
        """check loss rate with rate percent dropping

        options usage:
            rate:
                port rate percent at first round testing(0 ~ 100), default is 100.

            pdr:
                permit packet drop rate, , default is 0.

            drop_step:
                port rate percent drop step(0 ~ 100), default is 1.

            delay:
                warm up time before start main traffic. If it is set, it will
                start a delay time traffic to make sure packet generator
                under good status. Warm up flow is ignored by default.

            duration:
                traffic lasting time(second). Default value is 10 second.
        """
        loss_rate_table = []
        rate_percent = options.get("rate") or float(100)
        permit_loss_rate = options.get("pdr") or 0
        self.logger.info("allow loss rate: %f " % permit_loss_rate)
        rate_step = options.get("drop_step") or 1
        result = self._measure_loss(stream_ids, options)
        status = self._check_loss_rate(result, permit_loss_rate)
        loss_rate_table.append([rate_percent, result])
        # if first time loss rate is ok, ignore left flow
        if status:
            # return data is the same with dts/etgen format
            # In fact, multiple link peer have multiple loss rate value,
            # here only pick one
            tx_num, rx_num = list(result.values())[0][1:]
            return rate_percent, tx_num, rx_num
        _options = deepcopy(options)
        # if warm up option  'delay' is set, ignore it in next work flow
        if "delay" in _options:
            _options.pop("delay")
        if "rate" in _options:
            _options.pop("rate")
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
        tx_num, rx_num = list(last_result[1].values())[0][1:]
        return rate_percent, tx_num, rx_num

    def measure_rfc2544_with_pps(self, stream_ids=[], options={}):
        """
        check loss rate with pps bisecting.(not implemented)

        Currently, ixia/trex use rate percent to control port flow rate,
        pps not supported.
        """
        max_pps = options.get("max_pps")
        min_pps = options.get("min_pps")
        step = options.get("step") or 10000
        permit_loss_rate = options.get("permit_loss_rate") or 0.0001
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
            pps = (traffic_pps_max - traffic_pps_min) / 2 + traffic_pps_min

        self.logger.info("zero loss pps is %f" % pps)
        # use last result as return data to keep the same with dts/etgen format
        # In fact, multiple link peer have multiple loss rate value,
        # here only pick one
        return list(loss_pps_table[-1][1].values())[0]

    def measure_rfc2544_dichotomy(self, stream_ids=[], options={}):
        """check loss rate using dichotomy algorithm

        options usage:
            delay:
                warm up time before start main traffic. If it is set, it will
                start a delay time traffic to make sure packet generator
                under good status. Warm up flow is ignored by default.

            duration:
                traffic lasting time(second). Default value is 10 second.

            min_rate:
                lower bound rate percent , default is 0.

            max_rate:
                upper bound rate percent , default is 100.

            pdr:
                permit packet drop rate(<1.0), default is 0.

            accuracy :
                dichotomy algorithm accuracy, default 0.001.
        """
        if self.pktgen_type == PKTGEN_IXIA_NETWORK:
            return self._measure_rfc2544_ixnet(stream_ids, options)

        max_rate = options.get("max_rate") or 100.0
        min_rate = options.get("min_rate") or 0.0
        accuracy = options.get("accuracy") or 0.001
        permit_loss_rate = options.get("pdr") or 0.0
        duration = options.get("duration") or 10.0
        throughput_stat_flag = options.get("throughput_stat_flag") or False
        # start warm up traffic
        delay = options.get("delay")
        _options = {"duration": duration}
        if delay:
            self._prepare_transmission(stream_ids=stream_ids)
            self.__warm_up_pktgen(stream_ids, _options, delay)
            self._clear_streams()
        # traffic parameters for dichotomy algorithm
        loss_rate_table = []
        hit_result = None
        hit_rate = 0
        rate = traffic_rate_max = max_rate
        traffic_rate_min = min_rate
        while True:
            # run loss rate testing
            _options = {
                "throughput_stat_flag": throughput_stat_flag,
                "duration": duration,
            }
            result = self._measure_loss(stream_ids, _options)
            loss_rate_table.append([rate, result])
            status = self._check_loss_rate(
                result[0] if throughput_stat_flag else result, permit_loss_rate
            )
            # if upper bound rate percent hit, quit the left flow
            if rate == max_rate and status:
                hit_result = result
                hit_rate = rate
                break
            # if lower bound rate percent not hit, quit the left flow
            if rate == min_rate and not status:
                break
            if status:
                traffic_rate_min = rate
                hit_result = result
                hit_rate = rate
            else:
                traffic_rate_max = rate
            if traffic_rate_max - traffic_rate_min < accuracy:
                break
            rate = (traffic_rate_max - traffic_rate_min) / 2 + traffic_rate_min
            self._clear_streams()
            # set stream rate percent to custom value
            self._set_stream_rate_percent(rate)

        if throughput_stat_flag:
            if not hit_result or not hit_result[0]:
                msg = (
                    "expected permit loss rate <{0}> "
                    "not between rate {1} and rate {2}"
                ).format(permit_loss_rate, max_rate, min_rate)
                self.logger.error(msg)
                self.logger.info(pformat(loss_rate_table))
                ret_value = 0, result[0][0][1], result[0][0][2], 0
            else:
                self.logger.debug(pformat(loss_rate_table))
                ret_value = (
                    hit_rate,
                    hit_result[0][0][1],
                    hit_result[0][0][2],
                    hit_result[1][1],
                )
        else:
            if not hit_result:
                msg = (
                    "expected permit loss rate <{0}> "
                    "not between rate {1} and rate {2}"
                ).format(permit_loss_rate, max_rate, min_rate)
                self.logger.error(msg)
                self.logger.info(pformat(loss_rate_table))
                ret_value = 0, result[0][1], result[0][2]
            else:
                self.logger.debug(pformat(loss_rate_table))
                ret_value = hit_rate, hit_result[0][1], hit_result[0][2]
        self.logger.info("zero loss rate is %f" % hit_rate)

        return ret_value

    def measure(self, stream_ids, traffic_opt):
        """
        use as an unify interface method for packet generator
        """
        method = traffic_opt.get("method")
        if method == "throughput":
            result = self.measure_throughput(stream_ids, traffic_opt)
        elif method == "latency":
            result = self.measure_latency(stream_ids, traffic_opt)
        elif method == "loss":
            result = self.measure_loss(stream_ids, traffic_opt)
        elif method == "rfc2544":
            result = self.measure_rfc2544(stream_ids, traffic_opt)
        elif method == "rfc2544_with_pps":
            result = self.measure_rfc2544_with_pps(stream_ids, traffic_opt)
        elif method == "rfc2544_dichotomy":
            result = self.measure_rfc2544_dichotomy(stream_ids, traffic_opt)
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
            msg = (
                "packet generator <{0}> has no configuration " "in pktgen.cfg"
            ).format(self.pktgen_type)
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


class DpdkPacketGenerator(PacketGenerator):
    pass  # not implemented
