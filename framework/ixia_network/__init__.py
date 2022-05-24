# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2021 Intel Corporation
#

"""
ixNetwork package
"""
import os
import time
import traceback
from pprint import pformat

from .ixnet import IxnetTrafficGenerator
from .ixnet_config import IxiaNetworkConfig

__all__ = [
    "IxNetwork",
]


class IxNetwork(IxnetTrafficGenerator):
    """
    ixNetwork performance measurement class.
    """

    def __init__(self, name, config, logger):
        self.NAME = name
        self.logger = logger
        ixiaRef = self.NAME
        if ixiaRef not in config:
            return
        _config = config.get(ixiaRef, {})
        self.ixiaVersion = _config.get("Version")
        self.ports = _config.get("Ports")
        ixia_ip = _config.get("IP")
        rest_server_ip = _config.get("ixnet_api_server_ip")
        self.max_retry = int(_config.get("max_retry") or "5")  # times
        self.logger.debug(locals())
        rest_config = IxiaNetworkConfig(
            ixia_ip,
            rest_server_ip,
            "11009",
            [[ixia_ip, p.get("card"), p.get("port")] for p in self.ports],
        )
        super(IxNetwork, self).__init__(rest_config, logger)
        self._traffic_list = []
        self._result = None

    @property
    def OUTPUT_DIR(self):
        # get dts output folder path
        if self.logger.log_path.startswith(os.sep):
            output_path = self.logger.log_path
        else:
            cur_path = os.sep.join(os.path.realpath(__file__).split(os.sep)[:-2])
            output_path = os.path.join(cur_path, self.logger.log_path)
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        return output_path

    def get_ports(self):
        """
        get ixNetwork ports for dts `ports_info`
        """
        plist = []
        for p in self.ports:
            plist.append(
                {
                    "type": "ixia",
                    "pci": "IXIA:%d.%d" % (p["card"], p["port"]),
                }
            )
        return plist

    def send_ping6(self, pci, mac, ipv6):
        return "64 bytes from"

    def disconnect(self):
        """quit from ixNetwork api server"""
        self.tear_down()
        msg = "close ixNetwork session done !"
        self.logger.info(msg)

    def prepare_ixia_network_stream(self, traffic_list):
        self._traffic_list = []
        for txPort, rxPort, pcapFile, option in traffic_list:
            stream = self.configure_streams(pcapFile, option.get("fields_config"))
            tx_p = self.tg_vports[txPort]
            rx_p = self.tg_vports[rxPort]
            self._traffic_list.append((tx_p, rx_p, stream))

    def start(self, options):
        """start ixNetwork measurement"""
        test_mode = options.get("method")
        options["traffic_list"] = self._traffic_list
        self.logger.debug(pformat(options))
        if test_mode == "rfc2544_dichotomy":
            cnt = 0
            while cnt < self.max_retry:
                try:
                    result = self.send_rfc2544_throughput(options)
                    if result:
                        break
                except Exception as e:
                    msg = "failed to run rfc2544".format(cnt)
                    self.logger.error(msg)
                    self.logger.error(traceback.format_exc())
                cnt += 1
                msg = "No.{} rerun ixNetwork rfc2544".format(cnt)
                self.logger.warning(msg)
                time.sleep(10)
            else:
                result = []
        else:
            msg = "not support measurement {}".format(test_mode)
            self.logger.error(msg)
            self._result = None
            return None
        self.logger.info("measure <{}> completed".format(test_mode))
        self.logger.info(result)
        self._result = result
        return result

    def get_rfc2544_stat(self, port_list):
        """
        Get RX/TX packet statistics.
        """
        if not self._result:
            return [0] * 3

        result = self._result
        _ixnet_stats = {}
        for item in result:
            port_id = int(item.get("Trial")) - 1
            _ixnet_stats[port_id] = dict(item)
        port_stat = _ixnet_stats.get(0, {})
        rx_packets = float(port_stat.get("Agg Rx Count (frames)") or "0.0")
        tx_packets = float(port_stat.get("Agg Tx Count (frames)") or "0.0")
        rx_pps = float(port_stat.get("Agg Rx Throughput (fps)") or "0.0")
        return tx_packets, rx_packets, rx_pps

    def get_stats(self, ports, mode):
        """
        get statistics of custom mode
        """
        methods = {
            "rfc2544": self.get_rfc2544_stat,
        }
        if mode not in list(methods.keys()):
            msg = "not support mode <{0}>".format(mode)
            raise Exception(msg)
        # get custom mode stat
        func = methods.get(mode)
        stats = func(ports)

        return stats
