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
import os
import time
import traceback
from pprint import pformat

from .pktgen_base import PKTGEN_IXIA_NETWORK, PacketGenerator


class IxNetworkPacketGenerator(PacketGenerator):
    """
    ixNetwork packet generator
    """

    def __init__(self, tester):
        super(IxNetworkPacketGenerator, self).__init__(tester)
        self.pktgen_type = PKTGEN_IXIA_NETWORK
        self._conn = None
        # ixNetwork configuration information of dts
        conf_inst = self._get_generator_conf_instance()
        self.conf = conf_inst.load_pktgen_config()
        # ixNetwork port configuration
        self._traffic_ports = []
        self._ports = []
        self._rx_ports = []

    def get_ports(self):
        """used for ixNetwork packet generator"""
        return self._conn.get_ports()

    def _prepare_generator(self):
        """connect with ixNetwork api server"""
        try:
            self._connect(self.conf)
        except Exception as e:
            msg = "failed to connect to ixNetwork api server"
            raise Exception(msg)

    def _connect(self, conf):
        # initialize ixNetwork class
        from framework.ixia_network import IxNetwork

        self._conn = IxNetwork(self.pktgen_type, conf, self.logger)
        for p in self._conn.get_ports():
            self._ports.append(p)

        self.logger.debug(self._ports)

    def _disconnect(self):
        """
        disconnect with ixNetwork api server
        """
        try:
            self._remove_all_streams()
            self._conn.disconnect()
        except Exception as e:
            msg = "Error disconnecting: %s" % e
            self.logger.error(msg)
        self._conn = None

    def quit_generator(self):
        """close ixNetwork session"""
        if self._conn is not None:
            self._disconnect()

    def _get_port_pci(self, port_id):
        """
        get ixNetwork port pci address
        """
        for pktgen_port_id, info in enumerate(self._ports):
            if pktgen_port_id == port_id:
                _pci = info.get("pci")
                return _pci
        else:
            return None

    def _get_gen_port(self, pci):
        """
        get port management id of the packet generator
        """
        for pktgen_port_id, info in enumerate(self._ports):
            _pci = info.get("pci")
            if _pci == pci:
                return pktgen_port_id
        else:
            return -1

    def _is_gen_port(self, pci):
        """
        check if a pci address is managed by the packet generator
        """
        for name, _port_obj in self._conn.ports.items():
            _pci = _port_obj.info["pci_addr"]
            self.logger.debug((_pci, pci))
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
            ports.append("IXIA:%d" % idx)
        return ports

    def send_ping6(self, pci, mac, ipv6):
        """Send ping6 packet from IXIA ports."""
        return self._conn.send_ping6(pci, mac, ipv6)

    def _clear_streams(self):
        """clear streams in `PacketGenerator`"""
        # if streams has been attached, remove them from ixNetwork api server.
        self._remove_all_streams()

    def _remove_all_streams(self):
        """
        remove all stream deployed on the packet generator
        """
        if not self.get_streams():
            return

    def _check_options(self, opts={}):
        return True

    def _retrieve_port_statistic(self, stream_id, mode):
        """ixNetwork traffic statistics"""
        stats = self._conn.get_stats(self._traffic_ports, mode)
        stream = self._get_stream(stream_id)
        self.logger.debug(pformat(stream))
        self.logger.debug(pformat(stats))
        if mode == "rfc2544":
            return stats
        else:
            msg = "not support mode <{0}>".format(mode)
            raise Exception(msg)

    ##########################################################################
    #
    #  class ``PacketGenerator`` abstract methods should be implemented here
    #
    ##########################################################################
    def _prepare_transmission(self, stream_ids=[], latency=False):
        """add one/multiple streams in one/multiple ports"""
        port_config = {}

        for stream_id in stream_ids:
            stream = self._get_stream(stream_id)
            tx_port = stream.get("tx_port")
            rx_port = stream.get("rx_port")
            pcap_file = stream.get("pcap_file")
            # save port id list
            if tx_port not in self._traffic_ports:
                self._traffic_ports.append(tx_port)
            if rx_port not in self._traffic_ports:
                self._traffic_ports.append(rx_port)
            if rx_port not in self._rx_ports:
                self._rx_ports.append(rx_port)
            # set all streams in one port to do batch configuration
            options = stream["options"]
            if tx_port not in list(port_config.keys()):
                port_config[tx_port] = []
            config = {}
            config.update(options)
            # get stream rate percent
            stream_config = options.get("stream_config")
            rate_percent = stream_config.get("rate")
            # set port list input parameter of ixNetwork class
            ixia_option = [tx_port, rx_port, pcap_file, options]
            port_config[tx_port].append(ixia_option)

        self.rate_percent = rate_percent
        if not port_config:
            msg = "no stream options for ixNetwork packet generator"
            raise Exception(msg)

        port_lists = []
        for port_id, option in port_config.items():
            port_lists += option
        self._conn.prepare_ixia_network_stream(port_lists)

    def _start_transmission(self, stream_ids, options={}):
        # run ixNetwork api server
        try:
            # Start traffic on port(s)
            self.logger.info("begin traffic ......")
            self._conn.start(options)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.logger.error(e)

    def _stop_transmission(self, stream_id):
        if self._traffic_ports:
            self.logger.info("traffic completed. ")
