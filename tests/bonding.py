# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2019 Intel Corporation
#

import os
import re
import socket
import struct
import time
from socket import htonl

from scapy.sendrecv import sendp
from scapy.utils import wrpcap

import framework.utils as utils
from framework.exception import TimeoutException, VerifyFailure
from framework.packet import TMP_PATH, Packet
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE

# define bonding mode
MODE_ROUND_ROBIN = "ROUND_ROBIN(0)"
MODE_ACTIVE_BACKUP = "ACTIVE_BACKUP(1)"
MODE_XOR_BALANCE = "BALANCE(2)"
MODE_BROADCAST = "BROADCAST(3)"
MODE_LACP = "8023AD(4)"
MODE_TLB_BALANCE = "TLB(5)"
MODE_ALB_BALANCE = "ALB(6)"

# define packet size
FRAME_SIZE_64 = 64
FRAME_SIZE_128 = 128
FRAME_SIZE_256 = 256
FRAME_SIZE_512 = 512
FRAME_SIZE_1024 = 1024
FRAME_SIZE_1518 = 1518


class PmdBonding(object):
    """common methods for testpmd bonding"""

    def __init__(self, **kwargs):
        # set parent instance
        self.parent = kwargs.get("parent")
        # set target source code directory
        self.target_source = self.parent.dut.base_dir
        # set logger
        self.logger = self.parent.logger
        self.verify = self.parent.verify
        # select packet generator
        self.pktgen_name = "ixia" if self.is_perf else "scapy"
        # traffic default config
        self.default_pkt_size = kwargs.get("pkt_size") or FRAME_SIZE_64
        self.default_src_mac = kwargs.get("src_mac")
        self.default_src_ip = kwargs.get("src_ip")
        self.default_src_port = kwargs.get("src_port")
        self.default_dst_ip = kwargs.get("dst_ip")
        self.default_dst_port = kwargs.get("dst_port")
        self.default_pkt_name = kwargs.get("pkt_name")
        # testpmd
        self.testpmd = PmdOutput(self.parent.dut)
        self.testpmd_status = "close"

    #
    # On tester platform, packet transmission
    #
    def mac_str_to_int(self, mac_str):
        """convert the MAC type from the string into the int."""
        mac_hex = "0x"
        for mac_part in mac_str.split(":"):
            mac_hex += mac_part
        return int(mac_hex, 16)

    def mac_int_to_str(self, mac_int):
        """Translate the MAC type from the string into the int."""
        temp = hex(mac_int)[2:]
        b = []
        [b.append(temp[n : n + 2]) for n in range(len(temp)) if n % 2 == 0]
        new_mac = ":".join(b)
        return new_mac

    def ip_str_to_int(self, ip_str):
        """
        convert the IP type from the string into the int.
        """
        ip_int = socket.ntohl(struct.unpack("I", socket.inet_aton(str(ip_str)))[0])
        return ip_int

    def ip_int_to_str(self, ip_int):
        """
        convert the IP type from the int into the string.
        """
        ip_str = socket.inet_ntoa(struct.pack("I", socket.htonl(ip_int)))
        return ip_str

    def increase_ip(self, ip, step=1):
        """ip: string format"""
        _ip_int = self.ip_str_to_int(ip)
        new_ip = self.ip_int_to_str(_ip_int + step)
        return new_ip

    def increase_mac(self, mac, step=1):
        """mac: string format"""
        _mac_int = self.mac_str_to_int(mac)
        new_mac = self.mac_int_to_str(_mac_int + step)
        return new_mac

    def increase_port(self, port, step=1):
        """port: int format"""
        new_port = port + step
        return new_port

    def increase_mac_ip_port(self, step=1):
        # get source port setting
        mac, ip, port = (
            self.default_src_mac,
            self.default_src_ip,
            self.default_src_port,
        )
        return (
            self.increase_mac(mac, step),
            self.increase_ip(ip, step),
            self.increase_port(port, step),
        )

    def get_pkt_len(self, pkt_type):
        """get packet payload size"""
        frame_size = self.default_pkt_size
        headers_size = sum([HEADER_SIZE[x] for x in ["eth", "ip", pkt_type]])
        pktlen = frame_size - headers_size
        return pktlen

    def set_stream_to_slave_port(self, dut_port_id):
        """
        use framework/packet.py module to create one stream, send stream to
        slave port
        """
        # get dst port mac address
        pkt_name = self.default_pkt_name
        destport = self.default_dst_port
        destip = self.default_dst_ip
        dst_mac = self.get_port_info(dut_port_id, "mac")
        # packet size
        pktlen = self.get_pkt_len(pkt_name)
        # set stream configuration
        srcmac, srcip, srcport = self.increase_mac_ip_port(0)
        pkt_config = {
            "type": pkt_name.upper(),
            "pkt_layers": {
                # Ether(dst=nutmac, src=srcmac)
                "ether": {"src": srcmac, "dst": dst_mac},
                # IP(dst=destip, src=srcip, len=%s)
                "ipv4": {"src": srcip, "dst": destip},
                # pkt_name(sport=srcport, dport=destport)
                pkt_name: {"src": srcport, "dst": destport},
                # Raw(load='\x50'*%s)
                "raw": {"payload": ["58"] * self.get_pkt_len(pkt_name)},
            },
        }
        # create packet
        streams = []
        # keep a copy of pcap for debug
        savePath = os.sep.join([TMP_PATH, "pkt_{0}.pcap".format(pkt_name)])
        pkt_type = pkt_config.get("type")
        pkt_layers = pkt_config.get("pkt_layers")
        pkt = Packet(pkt_type=pkt_type.upper())
        for layer in list(pkt_layers.keys()):
            pkt.config_layer(layer, pkt_layers[layer])
        pkt.save_pcapfile(filename=savePath)
        streams.append(pkt.pktgen.pkt)

        return streams

    def set_stream_to_bond_port(self, bond_port, slaves):
        """
        : use framework/packet.py module to create multiple streams
          send streams from bond port to slaves
        :param bond_port:
            bonded device port id
        :param slaves:
            slaves port id
        """
        pkt_configs = []
        # get dst port mac address
        pkt_name = self.default_pkt_name
        destport = self.default_dst_port
        destip = self.default_dst_ip
        dst_mac = self.get_port_info(bond_port, "mac")
        # packet size
        pktlen = self.get_pkt_len(pkt_type)
        # set stream configuration
        for packet_id in range(len(slaves["active"])):
            srcmac, srcip, srcport = self.increase_mac_ip_port(packet_id)
            pkt_configs.append(
                {
                    "type": pkt_name.upper(),
                    "pkt_layers": {
                        # Ether(dst=nutmac, src=srcmac)
                        "ether": {"src": srcmac, "dst": dst_mac},
                        # IP(dst=destip, src=srcip, len=%s)
                        "ipv4": {"src": srcip, "dst": destip},
                        # pkt_name(sport=srcport, dport=destport)
                        pkt_name: {"src": srcport, "dst": destport},
                        # Raw(load='\x50'*%s)
                        "raw": {"payload": ["58"] * self.get_pkt_len(pkt_name)},
                    },
                }
            )
        # create packet
        streams = []
        for values in pkt_configs:
            # keep a copy of pcap for debug
            savePath = os.sep.join([TMP_PATH, "pkt_{0}.pcap".format(stm_name)])
            pkt_type = values.get("type")
            pkt_layers = values.get("pkt_layers")
            pkt = Packet(pkt_type=pkt_type.upper())
            for layer in list(pkt_layers.keys()):
                pkt.config_layer(layer, pkt_layers[layer])
            pkt.save_pcapfile(filename=savePath)
            streams.append(pkt.pktgen.pkt)

        return streams

    def send_packets_by_scapy(self, **kwargs):
        tx_iface = kwargs.get("port topo")[0]
        # set interface ready to send packet
        cmd = "ifconfig {0} up".format(tx_iface)
        self.parent.tester.send_expect(cmd, "# ", 30)
        send_pkts = kwargs.get("stream")
        # stream config
        stream_configs = kwargs.get("traffic configs")
        count = stream_configs.get("count")
        interval = stream_configs.get("interval", 0.01)
        # run traffic
        sendp(send_pkts, iface=tx_iface, inter=interval, verbose=False, count=count)

    def send_packets_by_ixia(self, **kwargs):
        tester_port = kwargs.get("tx_intf")
        count = kwargs.get("count", 1)
        traffic_type = kwargs.get("traffic_type", "normal")
        traffic_time = kwargs.get("traffic_time", 0)
        rate_percent = kwargs.get("rate_percent", float(100))
        # ---------------------------------------------------------------
        send_pkts = []
        self.tgen_input = []
        tgen_input = self.tgen_input
        # generate packet contain multi stream
        for pkt in list(self.packet_types.values()):
            send_pkts.append(pkt.pktgen.pkt)
        ixia_pkt = os.sep.join([self.target_source, "bonding_ixia.pcap"])
        wrpcap(ixia_pkt, send_pkts)
        # ----------------------------------------------------------------
        # set packet for send
        # pause frame basic configuration
        pause_time = 65535
        pause_rate = 0.50
        # run ixia testing
        frame_size = self.default_pkt_size
        # calculate number of packets
        expect_pps = self.parent.wirespeed(self.parent.nic, frame_size, 1) * 1000000.0
        # get line rate
        linerate = expect_pps * (frame_size + 20) * 8
        # calculate default sleep time for one pause frame
        sleep = (1 / linerate) * pause_time * 512
        # calculate packets dropped in sleep time
        self.n_pkts = int((sleep / (1 / expect_pps)) * (1 / pause_rate))
        # ----------------------------------------------------------------
        tester_port = self.parent.tester.get_local_port(self.parent.dut_ports[0])
        tgen_input.append((tester_port, tester_port, ixia_pkt))
        # run latency stat statistics
        self.parent.tester.loop_traffic_generator_throughput(
            tgen_input, self.rate_percent
        )

    def stop_ixia(self, data_types="packets"):
        tester_inst = self.parent.tester
        # get ixia statistics
        line_rate = tester_inst.get_port_line_rate()
        rx_bps, rx_pps = tester_inst.stop_traffic_generator_throughput_loop(
            self.tgen_input
        )
        output = tester_inst.traffic_get_port_stats(self.tgen_input)
        self.cur_data["ixia statistics"] = []
        append = self.cur_data["ixia statistics"].append
        append("send packets: {0}".format(output[0]))
        append("line_rate: {0}".format(line_rate[0]))
        append("rate_percent: {0}%".format(self.rate_percent))

    def get_pktgen(self, name):
        pkt_gens = {
            "ixia": self.send_packets_by_ixia,
            "scapy": self.send_packets_by_scapy,
        }
        pkt_generator = pkt_gens.get(name)

        return pkt_generator

    def send_packet(self, traffic_config):
        """
        stream transmission on specified link topology
        """
        time.sleep(2)
        # start traffic
        self.logger.info("begin transmission ...")
        pktgen = self.get_pktgen(self.pktgen_name)
        result = pktgen(**traffic_config)
        # end traffic
        self.logger.info("complete transmission")

        return result

    #
    # On dut, dpdk testpmd common methods
    #
    def check_process_status(self, process_name="testpmd"):
        cmd = "ps aux | grep -i %s | grep -v grep | awk {'print $2'}" % (process_name)
        out = self.parent.dut.alt_session.send_expect(cmd, "# ", 10)
        status = True if out != "" else False
        return status

    def check_process_exist(self, process_name="testpmd"):
        status = self.check_process_status(process_name)
        if not status:
            msg = "{0} process exceptional quit".format(process_name)
            out = self.parent.dut.session.session.get_output_all()
            self.logger.info(out)
            raise VerifyFailure(msg)

    def d_console(self, cmds):
        """wrap up testpmd command interactive console"""
        if len(cmds) == 0:
            return
        # check if cmds is string
        if isinstance(cmds, str):
            timeout = 10
            cmds = [[cmds, "", timeout]]
        # check if cmds is only one command
        if not isinstance(cmds[0], list):
            cmds = [cmds]
        outputs = [] if len(cmds) > 1 else ""
        for item in cmds:
            expected_items = item[1]
            if expected_items and isinstance(expected_items, (list, tuple)):
                check_output = True
                expected_str = expected_items[0] or "testpmd> "
            else:
                check_output = False
                expected_str = expected_items or "testpmd> "
            timeout = int(item[2]) if len(item) == 3 else 5
            # ----------------------------------------------------------------
            # run command on session
            try:
                console = self.testpmd.execute_cmd
                msg_pipe = self.testpmd.get_output
                output = console(item[0], expected_str, timeout)
                output = msg_pipe(timeout) if not output else output
            except TimeoutException:
                try:
                    # check if testpmd quit
                    self.check_process_exist()
                except Exception as e:
                    self.testpmd_status = "close"
                msg = "execute '{0}' timeout".format(item[0])
                output = out = self.parent.dut.session.session.get_output_all()
                self.logger.error(output)
                raise Exception(msg)

            if len(cmds) > 1:
                outputs.append(output)
            else:
                outputs = output
            if check_output and len(expected_items) >= 2:
                self.logger.info(output)
                expected_output = expected_items[1]
                check_type = True if len(expected_items) == 2 else expected_items[2]
                if check_type and expected_output in output:
                    msg = "expected '{0}' is in output".format(expected_output)
                    self.logger.info(msg)
                elif not check_type and expected_output not in output:
                    fmt = "unexpected '{0}' is not in output"
                    msg = fmt.format(expected_output)
                    self.logger.info(msg)
                else:
                    status = "isn't in" if check_type else "is in"
                    msg = "[{0}] {1} output".format(expected_output, status)
                    self.logger.error(msg)
                    raise VerifyFailure(msg)

        time.sleep(2)
        return outputs

    def preset_testpmd(self, core_mask, options="", eal_param=""):
        try:
            self.testpmd.start_testpmd(
                core_mask, param=" ".join(options), eal_param=eal_param
            )
        except TimeoutException:
            # check if testpmd quit
            try:
                self.check_process_exist()
            except Exception as e:
                self.testpmd_status = "close"
            msg = "execute '{0}' timeout".format(item[0])
            self.logger.error(msg_pipe(timeout))
            raise TimeoutException(msg)
        # wait lsc event udpate done
        time.sleep(10)
        # check if testpmd has bootep up
        if self.check_process_status():
            self.logger.info("testpmd boot up successful")
        else:
            raise VerifyFailure("testpmd boot up failed")
        self.d_console(self.preset_testpmd_cmds)
        self.preset_testpmd_cmds = []
        time.sleep(1)

    def start_testpmd(self, eal_option=""):
        if self.testpmd_status == "running":
            return
        # boot up testpmd
        hw_mask = "all"
        options = ""
        self.preset_testpmd_cmds = ["port stop all", "", 15]
        self.preset_testpmd(hw_mask, options, eal_param=eal_option)
        self.testpmd_status = "running"

    def stop_testpmd(self):
        time.sleep(1)
        testpmd_cmds = [
            ["port stop all", "", 15],
            ["show port stats all", ""],
            ["stop", ""],
        ]
        output = self.d_console(testpmd_cmds)
        time.sleep(1)
        return output

    def close_testpmd(self):
        if self.testpmd_status == "close":
            return None
        output = self.stop_testpmd()
        time.sleep(1)
        self.testpmd.quit()
        time.sleep(10)
        if self.check_process_status():
            raise VerifyFailure("testpmd close failed")
        else:
            self.logger.info("close testpmd successful")
        self.testpmd_status = "close"
        return output

    def start_ports(self, port="all"):
        """
        Start a port which the testpmd can see.
        """
        timeout = 12 if port == "all" else 5
        cmds = [
            ["port start %s" % str(port), " ", timeout],
            # to avoid lsc event message interfere normal status
            [" ", "", timeout],
        ]
        self.d_console(cmds)

    def get_stats(self, portid, flow=["rx", "tx"]):
        """
        get one port statistics of testpmd
        """
        _portid = int(portid) if isinstance(portid, str) else portid
        info = self.testpmd.get_pmd_stats(_portid)
        _kwd = ["-packets", "-errors", "-bytes"]
        stats = {}
        if isinstance(flow, list):
            for item in flow:
                for item2 in _kwd:
                    name = item.upper() + item2
                    stats[name] = int(info[name])
        elif isinstance(flow, str):
            for item in _kwd:
                name = flow.upper() + item
                stats[name] = int(info[name])
        else:
            msg = "unknown data type"
            raise Exception(msg)

        return stats

    def get_all_stats(self, ports):
        """
        Get a group of ports statistics, which testpmd can display.
        """
        stats = {}
        attrs = ["tx", "rx"]
        for port_id in ports:
            stats[port_id] = self.get_stats(port_id, attrs)

        return stats

    def set_tester_port_status(self, port_name, status):
        """
        Do some operations to the network interface port,
        such as "up" or "down".
        """
        eth = self.parent.tester.get_interface(port_name)
        self.parent.tester.admin_ports_linux(eth, status)
        time.sleep(5)

    def set_dut_peer_port_by_id(self, port_id, status):
        # stop peer port on tester
        intf = self.parent.tester.get_local_port(self.parent.dut_ports[port_id])
        self.set_tester_port_status(intf, status)
        time.sleep(5)
        cur_status = self.get_port_info(port_id, "link_status")
        self.logger.info("port {0} is [{1}]".format(port_id, cur_status))
        if cur_status != status:
            self.logger.warning("expected status is [{0}]".format(status))

    def set_dut_port_status(self, port_id, status):
        opt = "link-up" if status == "up" else "link-down"
        # stop slave link by force
        cmd = "set {0} port {1}".format(opt, port_id)
        self.d_console(cmd)
        time.sleep(5)
        cur_status = self.get_port_info(port_id, "link_status")
        self.logger.info("port {0} is [{1}]".format(port_id, cur_status))
        if cur_status != status:
            self.logger.warning("expected status is [{0}]".format(status))

    #
    # testpmd bonding commands
    #
    def get_value_from_str(self, key_str, regx_str, string):
        """
        Get some values from the given string by the regular expression.
        """
        if isinstance(key_str, str):
            pattern = r"(?<=%s)%s" % (key_str, regx_str)
            s = re.compile(pattern)
            res = s.search(string)
            if type(res).__name__ == "NoneType":
                msg = "{0} hasn't match anything".format(key_str)
                self.logger.warning(msg)
                return " "
            else:
                return res.group(0)
        elif isinstance(key_str, (list, tuple)):
            for key in key_str:
                pattern = r"(?<=%s)%s" % (key, regx_str)
                s = re.compile(pattern)
                res = s.search(string)
                if type(res).__name__ == "NoneType":
                    continue
                else:
                    return res.group(0)
            else:
                self.logger.warning("all key_str hasn't match anything")
                return " "

    def _get_detail_from_port_info(self, port_id, args):
        """
        Get the detail info from the output of pmd cmd
            'show port info <port num>'.
        """
        key_str, regx_str = args
        out = self.d_console("show port info %d" % port_id)
        find_value = self.get_value_from_str(key_str, regx_str, out)
        return find_value

    def get_detail_from_port_info(self, port_id, args):
        if isinstance(args[0], (list, tuple)):
            return [
                self._get_detail_from_port_info(port_id, sub_args) for sub_args in args
            ]
        else:
            return self._get_detail_from_port_info(port_id, args)

    def get_port_info(self, port_id, info_type):
        """
        Get the specified port information by its output message format
        """
        info_set = {
            "mac": ["MAC address: ", "([0-9A-F]{2}:){5}[0-9A-F]{2}"],
            "connect_socket": ["Connect to socket: ", "\d+"],
            "memory_socket": ["memory allocation on the socket: ", "\d+"],
            "link_status": ["Link status: ", "\S+"],
            "link_speed": ["Link speed: ", "\d+"],
            "link_duplex": ["Link duplex: ", "\S+"],
            "promiscuous_mode": ["Promiscuous mode: ", "\S+"],
            "allmulticast_mode": ["Allmulticast mode: ", "\S+"],
            "vlan_offload": [
                ["strip ", "\S+"],
                ["filter", "\S+"],
                ["qinq\(extend\) ", "\S+"],
            ],
            "queue_config": [
                ["Max possible RX queues: ", "\d+"],
                ["Max possible number of RXDs per queue: ", "\d+"],
                ["Min possible number of RXDs per queue: ", "\d+"],
                ["Max possible TX queues: ", "\d+"],
                ["Max possible number of TXDs per queue: ", "\d+"],
                ["Min possible number of TXDs per queue: ", "\d+"],
            ],
        }

        if info_type in list(info_set.keys()):
            return self.get_detail_from_port_info(port_id, info_set[info_type])
        else:
            msg = os.linesep.join(
                [
                    "support query items including::",
                    os.linesep.join(list(info_set.keys())),
                ]
            )
            self.logger.warning(msg)
            return None

    #
    # On dut, dpdk testpmd common bonding methods
    #
    def get_bonding_config(self, config_content, args):
        """
        Get bonding info by command "show bonding config".
        """
        key_str, regx_str = args
        find_value = self.get_value_from_str(key_str, regx_str, config_content)
        return find_value

    def get_info_from_bond_config(self, config_content, args):
        """
        Get active slaves of the bonding device which you choose.
        """
        search_args = args if isinstance(args[0], (list, tuple)) else [args]
        for search_args in search_args:
            try:
                info = self.get_bonding_config(config_content, search_args)
                break
            except Exception as e:
                self.logger.info(e)
        else:
            info = None

        return info

    def get_bonding_info(self, bond_port, info_types):
        """Get the specified port information by its output message format"""
        info_set = {
            "mode": ["Bonding mode: ", "\S*"],
            "agg_mode": ["IEEE802.3AD Aggregator Mode: ", "\S*"],
            "balance_policy": ["Balance Xmit Policy: ", "\S+"],
            "slaves": [
                ["Slaves \(\d\): \[", "\d*( \d*)*"],
                ["Slaves: \[", "\d*( \d*)*"],
            ],
            "active_slaves": [
                ["Active Slaves \(\d\): \[", "\d*( \d*)*"],
                ["Acitve Slaves: \[", "\d*( \d*)*"],
            ],
            "current_primary": ["Current Primary: \[", "\d*"],
        }
        # get all config information
        config_content = self.d_console("show bonding config %d" % bond_port)
        if isinstance(info_types, (list or tuple)):
            query_values = []
            for info_type in info_types:
                if info_type in list(info_set.keys()):
                    find_value = self.get_info_from_bond_config(
                        config_content, info_set[info_type]
                    )
                    if info_type in ["active_slaves", "slaves"]:
                        find_value = [value for value in find_value.split(" ") if value]
                else:
                    find_value = None
                query_values.append(find_value)
            return query_values
        else:
            info_type = info_types
            if info_type in list(info_set.keys()):
                find_value = self.get_info_from_bond_config(
                    config_content, info_set[info_type]
                )
                if info_type in ["active_slaves", "slaves"]:
                    find_value = [value for value in find_value.split(" ") if value]
                return find_value
            else:
                return None

    def get_active_slaves(self, bond_port):
        primary_port = int(self.get_bonding_info(bond_port, "current_primary"))
        active_slaves = self.get_bonding_info(bond_port, "active_slaves")

        return int(primary_port), [int(slave) for slave in active_slaves]

    def create_bonded_device(self, mode="", socket=0, verify_detail=False):
        """
        Create a bonding device with the parameters you specified.
        """
        p = r"\w+\((\d+)\)"
        mode_id = int(re.match(p, mode).group(1))
        cmd = "create bonded device %d %d" % (mode_id, socket)
        out = self.d_console(cmd)
        err_fmt = "Create bonded device on mode [%s] socket [%d] failed"
        self.verify("Created new bonded device" in out, err_fmt % (mode, socket))
        fmts = [
            "Created new bonded device net_bond_testpmd_[\d] on \(port ",
            "Created new bonded device net_bonding_testpmd_[\d] on \(port ",
            "Created new bonded device eth_bond_testpmd_[\d] on \(port ",
        ]
        bond_port = self.get_value_from_str(fmts, "\d+", out)
        bond_port = int(bond_port)

        if verify_detail:
            out = self.d_console("show bonding config %d" % bond_port)
            self.verify(
                "Bonding mode: %s" % mode in out,
                "Bonding mode display error when create bonded device",
            )
            self.verify(
                "Slaves: []" in out, "Slaves display error when create bonded device"
            )
            self.verify(
                "Active Slaves: []" in out,
                "Active Slaves display error when create bonded device",
            )
            self.verify(
                "Current Primary: []" not in out,
                "Current Primary display error when create bonded device",
            )
            out = self.d_console("show port info %d" % bond_port)
            self.verify(
                "Connect to socket: %d" % socket in out,
                "Bonding port connect socket error",
            )
            self.verify(
                "Link status: down" in out, "Bonding port default link status error"
            )
            self.verify(
                "Link speed: 0 Mbps" in out, "Bonding port default link speed error"
            )

        return bond_port

    def add_slave(self, bond_port, invert_verify=False, expected_str="", *slave_ports):
        """
        Add ports into the bonding device as slaves.
        """
        if len(slave_ports) <= 0:
            utils.RED("No port exist when add slave to bonded device")
        for slave_id in slave_ports:
            cmd = "add bonding slave %d %d" % (slave_id, bond_port)
            out = self.d_console(cmd)
            if expected_str:
                self.verify(
                    expected_str in out, "message <{0}> is missing".format(expected_str)
                )
            slaves = self.get_bonding_info(bond_port, "slaves")
            if not invert_verify:
                self.verify(str(slave_id) in slaves, "Add port as bonding slave failed")
            else:
                err = "Add port as bonding slave successfully,should fail"
                self.verify(str(slave_id) not in slaves, err)

    def remove_slaves(self, bond_port, invert_verify=False, *slave_port):
        """
        Remove the specified slave port from the bonding device.
        """
        if len(slave_port) <= 0:
            msg = "No port exist when remove slave from bonded device"
            self.logger.error(msg)
        for slave_id in slave_port:
            cmd = "remove bonding slave %d %d" % (int(slave_id), bond_port)
            self.d_console(cmd)
            slaves = self.get_bonding_info(bond_port, "slaves")
            if not invert_verify:
                self.verify(
                    str(slave_id) not in slaves,
                    "Remove slave to fail from bonding device",
                )
            else:
                err = (
                    "Remove slave successfully from bonding device, " "should be failed"
                )
                self.verify(str(slave_id) in slaves, err)

    def remove_all_slaves(self, bond_port):
        """
        Remove all slaves of specified bound device.
        """
        all_slaves = self.get_bonding_info(bond_port, "slaves")
        if not all_slaves:
            return
        all_slaves = all_slaves.split()
        if len(all_slaves) == 0:
            return
        self.remove_slaves(bond_port, False, *all_slaves)

    def set_primary_slave(self, bond_port, slave_port, invert_verify=False):
        """
        Set the primary slave for the bonding device.
        """
        cmd = "set bonding primary %d %d" % (slave_port, bond_port)
        self.d_console(cmd)
        out = self.get_bonding_info(bond_port, "current_primary")
        if not invert_verify:
            self.verify(str(slave_port) in out, "Set bonding primary port failed")
        else:
            err = "Set bonding primary port successfully, should not success"
            self.verify(str(slave_port) not in out, err)

    def set_bonding_mode(self, bond_port, mode):
        """
        Set the bonding mode for port_id.
        """
        cmd = "set bonding mode %d %d" % (mode, bond_port)
        self.d_console(cmd)
        mode_value = self.get_bonding_info(bond_port, "mode")
        self.verify(str(mode) in mode_value, "Set bonding mode failed")

    def set_bonding_mac(self, bond_port, mac):
        """
        Set the MAC for the bonding device.
        """
        cmd = "set bonding mac_addr %s %s" % (bond_port, mac)
        self.d_console(cmd)
        new_mac = self.get_port_mac(bond_port)
        self.verify(new_mac == mac, "Set bonding mac failed")

    def get_port_mac(self, bond_port, query_type):
        bond_port_mac = self.get_port_info(bond_port, query_type)
        return bond_port_mac

    def set_bonding_balance_policy(self, bond_port, policy):
        """
        Set the balance transmit policy for the bonding device.
        """
        cmd = "set bonding balance_xmit_policy %d %s" % (bond_port, policy)
        self.d_console(cmd)
        new_policy = self.get_bonding_info(bond_port, "balance_policy")
        policy = "BALANCE_XMIT_POLICY_LAYER" + policy.lstrip("l")
        self.verify(new_policy == policy, "Set bonding balance policy failed")

    @property
    def is_perf(self):
        return self.parent._enable_perf
