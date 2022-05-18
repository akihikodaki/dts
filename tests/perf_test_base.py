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
Layer-3 forwarding test script base class.
"""
import json
import os
import re
import time
import traceback
from copy import deepcopy
from enum import Enum, unique
from itertools import product
from pprint import pformat

import numpy as np

import framework.utils as utils
from framework.config import SuiteConf
from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.pktgen import (
    PKTGEN_IXIA,
    PKTGEN_IXIA_NETWORK,
    PKTGEN_TREX,
    TRANSMIT_CONT,
)
from framework.utils import convert_int2ip, convert_ip2int

VF_L3FWD_NIC_SUPPORT = frozenset(
    (
        "IXGBE_10G-82599_SFP",
        "I40E_40G-QSFP_A",
        "I40E_25G-25G_SFP28",
        "I40E_10G-SFP_XL710",
        "ICE_100G-E810C_QSFP",
        "ICE_25G-E810C_SFP",
        "ICE_25G-E810_XXV_SFP",
    )
)


@unique
class BIN_TYPE(Enum):
    L3FWD = "l3fwd"
    PMD = "testpmd"


@unique
class SUITE_TYPE(Enum):
    VF = "vf_l3fwd"
    PF = "pf_l3fwd"


@unique
class SUITE_NAME(Enum):
    VF_KERNELPF = "vf_l3fwd_kernelpf"
    TESTPMD_PERF = "testpmd_perf"


@unique
class NIC_DRV(Enum):
    PCI_STUB = "pci-stub"  # linux system default driver, pci-stub
    IGB_UIO = "igb_uio"  # dpdk nic driver
    VFIO_PCI = "vfio-pci"


@unique
class MATCH_MODE(Enum):
    # LPM(longest prefix match) mode
    LPM = "lpm"
    # EM(Exact-Match) mode
    EM = "em"


# stream internet protocol layer types
@unique
class IP_TYPE(Enum):
    V6 = "ipv6"
    V4 = "ipv4"


@unique
class STREAM_TYPE(Enum):
    TCP = "TCP"
    UDP = "UDP"
    RAW = "RAW"


@unique
class STAT_ALGORITHM(Enum):
    ONE = "one"
    MEAN = "mean"


HEADER_SIZE = {
    "ether": 18,
    "ipv4": 20,
    "ipv6": 40,
    "udp": 8,
    "tcp": 20,
    "vlan": 8,
}


def get_enum_name(value, enum_cls):
    for _, enum_name in list(enum_cls.__members__.items()):
        if value == enum_name.value:
            return enum_name
    else:
        msg = f"{value} not define in Enum class {enum_cls}"
        raise Exception(msg)


class PerfTestBase(object):
    def __init__(self, valports, socket, mode=None, bin_type=None):
        self.__bin_type = bin_type or BIN_TYPE.L3FWD
        self.__compile_rx_desc = None
        self.__rxtx_queue_size = None
        self.__mode = mode or SUITE_TYPE.PF
        self.__suite = None
        self.__valports = valports
        self.__socket = socket
        self.__core_offset = 2
        self.__nic_name = self.nic
        self.__pkt_typ = STREAM_TYPE.RAW
        self.__vf_driver = None
        self.__pf_driver = None
        self.__vf_ports_info = None

        self.__is_bin_ps_on = None
        self.__bin_ps_allow_list = None
        self.__bin_ps_restart = True
        self.__pre_bin_ps_cmd = None
        self.__bin_ps_wait_up = 0
        self.__traffic_stop_wait_time = 0
        self.__is_pmd_on = None
        self.__pmd_session = None
        self.__cur_case = None
        self.__json_results = {}

    @property
    def __output_path(self):
        suiteName = self.suite_name
        if self.logger.log_path.startswith(os.sep):
            output_path = os.path.join(self.logger.log_path, suiteName)
        else:
            cur_path = os.sep.join(os.path.realpath(__file__).split(os.sep)[:-2])
            output_path = os.path.join(cur_path, self.logger.log_path)
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        return output_path

    @property
    def __target_dir(self):
        target_dir = (
            "/root" + self.dut.base_dir[1:]
            if self.dut.base_dir.startswith("~")
            else self.dut.base_dir
        )
        return target_dir

    @property
    def __sockets(self):
        sockets = [
            cpu.get("socket") for cpu in self.dut.get_all_cores() if cpu.get("socket")
        ]
        total = len(set(sockets))
        self.verify(total > 0, "cpu socket should not be zero")
        return total

    @property
    def __core_thread_num(self):
        cpu_topos = self.dut.get_all_cores()
        core_index = cpu_topos[-1]["core"]
        thread_index = int(cpu_topos[-1]["thread"])
        if not core_index:
            msg = "wrong core index"
            raise VerifyFailure(msg)
        if not thread_index:
            msg = "wrong thread index"
            raise VerifyFailure(msg)
        return thread_index // core_index

    def __host_pmd_con(self, cmd):
        if not self.__pmd_session:
            return
        _cmd = [cmd, "# ", 10] if isinstance(cmd, str) else cmd
        output = self.__pmd_session.session.send_expect(*_cmd)
        return output

    def d_con(self, cmd):
        _cmd = [cmd, "# ", 10] if isinstance(cmd, (str)) else cmd
        return self.dut.send_expect(*_cmd)

    def __get_ipv4_lpm_vm_config(self, lpm_config):
        netaddr, mask = lpm_config.split("/")
        ip_range = int("1" * (32 - int(mask)), 2)
        start_ip = convert_int2ip(convert_ip2int(netaddr) + 1)
        end_ip = convert_int2ip(convert_ip2int(start_ip) + ip_range - 1)
        layers = {
            "ipv4": {
                "src": start_ip,
            },
        }
        fields_config = {
            "ip": {
                "src": {
                    "start": start_ip,
                    "end": end_ip,
                    "step": 1,
                    "action": "random",
                },
            },
        }
        return layers, fields_config

    def __get_ipv6_lpm_vm_config(self, lpm_config):
        netaddr, mask = lpm_config.split("/")
        ip_range = int("1" * (128 - int(mask)), 2)
        start_ip = convert_int2ip(convert_ip2int(netaddr, ip_type=6) + 1, ip_type=6)
        end_ip = convert_int2ip(
            convert_ip2int(start_ip, ip_type=6) + ip_range - 1, ip_type=6
        )
        layers = {
            "ipv6": {
                "src": start_ip,
            },
        }
        fields_config = {
            "ipv6": {
                "src": {
                    "start": start_ip,
                    "end": end_ip,
                    "step": 1,
                    "action": "random",
                },
            },
        }
        return layers, fields_config

    def __get_pkt_layers(self, pkt_type):
        if pkt_type in list(Packet.def_packet.keys()):
            return deepcopy(Packet.def_packet.get(pkt_type).get("layers"))
        local_def_packet = {
            "IPv6_RAW": ["ether", "ipv6", "raw"],
        }
        layers = local_def_packet.get(pkt_type)
        if not layers:
            msg = f"{pkt_type} not set in framework/packet.py, nor in local"
            raise VerifyFailure(msg)
        return layers

    def __get_pkt_len(self, pkt_type, ip_type="ip", frame_size=64):
        layers = self.__get_pkt_layers(pkt_type)
        if "raw" in layers:
            layers.remove("raw")
        headers_size = sum(map(lambda x: HEADER_SIZE[x], layers))
        pktlen = frame_size - headers_size
        return pktlen

    def __get_frame_size(self, name, frame_size):
        if self.pktgen_type is PKTGEN_IXIA_NETWORK:
            # ixNetwork api server will set ipv6 packet size to 78 bytes when
            # set frame size < 78.
            _frame_size = 78 if name is IP_TYPE.V6 and frame_size == 64 else frame_size
        else:
            _frame_size = 66 if name is IP_TYPE.V6 and frame_size == 64 else frame_size
        return _frame_size

    def __get_pkt_type_name(self, ip_layer):
        if ip_layer is IP_TYPE.V4:
            name = (
                "IP_RAW" if self.__pkt_typ == STREAM_TYPE.RAW else self.__pkt_typ.value
            )
        else:
            name = "IPv6_" + self.__pkt_typ.value
        return name

    def __config_stream(self, stm_name, layers=None, frame_size=64):
        _framesize = self.__get_frame_size(stm_name, frame_size)
        payload_size = self.__get_pkt_len(
            self.__get_pkt_type_name(stm_name),
            "ip" if stm_name is IP_TYPE.V4 else "ipv6",
            _framesize,
        )
        # set streams for traffic
        pkt_configs = {
            IP_TYPE.V4: {
                "type": self.__get_pkt_type_name(IP_TYPE.V4),
                "pkt_layers": {"raw": {"payload": ["58"] * payload_size}},
            },
            IP_TYPE.V6: {
                "type": self.__get_pkt_type_name(IP_TYPE.V6),
                "pkt_layers": {"raw": {"payload": ["58"] * payload_size}},
            },
        }
        if stm_name not in pkt_configs.keys():
            msg = "{} not set in table".format(stm_name)
            raise VerifyFailure(msg)
        values = deepcopy(pkt_configs.get(stm_name))
        if layers:
            values["pkt_layers"].update(layers)
        self.logger.debug(pformat(values))
        pkt = self.__get_pkt_inst(values)

        return pkt

    def __get_pkt_inst(self, pkt_config):
        pkt_type = pkt_config.get("type")
        pkt_layers = pkt_config.get("pkt_layers")
        _layers = self.__get_pkt_layers(pkt_type)
        if pkt_type not in Packet.def_packet.keys():
            pkt = Packet()
            pkt.pkt_cfgload = True
            pkt.assign_layers(_layers)
        else:
            pkt = Packet(pkt_type=pkt_type)
        for layer in list(pkt_layers.keys()):
            if layer not in _layers:
                continue
            pkt.config_layer(layer, pkt_layers[layer])
        self.logger.debug(pformat(pkt.pktgen.pkt.command()))

        return pkt.pktgen.pkt

    def __get_mac_layer(self, port_id):
        if self.__mode is SUITE_TYPE.VF:
            smac = self.__vf_ports_info[port_id]["src_mac"]
            dmac = self.__vf_ports_info[port_id]["vf_mac"]
            layer = {
                "ether": {
                    "src": smac,
                    "dst": dmac,
                },
            }
        else:
            if self.__bin_type is BIN_TYPE.PMD and self.kdriver == "ice":
                # testpmd can't use port real mac address to create traffic
                # packet when use Intel® Ethernet 800 Series nics.
                dmacs = [
                    "52:00:00:00:00:00",
                    "52:00:00:00:00:01",
                    "52:00:00:00:00:02",
                    "52:00:00:00:00:03",
                ]
                layer = {
                    "ether": {
                        "dst": dmacs[self.__valports.index(port_id)],
                        "src": "02:00:00:00:00:0%d" % port_id,
                    },
                }
            else:
                dmac = self.dut.get_mac_address(port_id)
                layer = {
                    "ether": {
                        "dst": dmac,
                        "src": "02:00:00:00:00:0%d" % port_id,
                    },
                }
        return layer

    def __preset_flows_configs(self):
        flows = self.__test_content.get("flows")
        if not flows:
            msg = "flows not set in json cfg file"
            raise VerifyFailure(msg)
        flows_configs = {}
        for name, mode_configs in flows.items():
            _name = get_enum_name(name.lower(), IP_TYPE)
            for mode, configs in mode_configs.items():
                _mode = get_enum_name(mode.lower(), MATCH_MODE)
                for index, config in enumerate(configs):
                    if _mode is MATCH_MODE.LPM:
                        # under LPM mode, one port only set one stream
                        if index >= len(self.__valports):
                            break
                        port_id = self.__valports[index]
                        _layer = self.__get_mac_layer(port_id)
                        _layer2, fields_config = (
                            self.__get_ipv4_lpm_vm_config(config)
                            if _name is IP_TYPE.V4
                            else self.__get_ipv6_lpm_vm_config(config)
                        )
                        _layer.update(_layer2)
                    else:
                        if index >= 2 * len(self.__valports):
                            break
                        port_id = self.__valports[int(index / 2) % len(self.__valports)]
                        _layer = self.__get_mac_layer(port_id)
                        _layer.update(config)
                        fields_config = None
                    flows_configs.setdefault((_name, _mode), []).append(
                        [_layer, fields_config]
                    )
        return flows_configs

    def __preset_streams(self):
        frame_sizes = self.__test_content.get("frame_sizes")
        if not frame_sizes:
            msg = "frame sizes not set in json cfg file"
            raise VerifyFailure(msg)
        test_streams = {}
        flows_configs = self.__preset_flows_configs()
        for frame_size in frame_sizes:
            for flow_key, flows_config in flows_configs.items():
                streams_key = flow_key + (frame_size,)
                for flow_config in flows_config:
                    _layers, fields_config = flow_config
                    pkt = self.__config_stream(flow_key[0], _layers, frame_size)
                    test_streams.setdefault(streams_key, []).append(
                        [pkt, fields_config]
                    )
        self.logger.debug(pformat(test_streams))
        return test_streams

    def __add_stream_to_pktgen(self, streams, option):
        def port(index):
            p = self.tester.get_local_port(self.__valports[index])
            return p

        topos = (
            [
                [port(index), port(index - 1)]
                if index % 2
                else [port(index), port(index + 1)]
                for index, _ in enumerate(self.__valports)
            ]
            if len(self.__valports) > 1
            else [[port(0), port(0)]]
        )
        stream_ids = []
        step = int(len(streams) / len(self.__valports))
        for cnt, stream in enumerate(streams):
            pkt, fields_config = stream
            index = cnt // step
            txport, rxport = topos[index]
            _option = deepcopy(option)
            _option["pcap"] = pkt
            if fields_config:
                _option["fields_config"] = fields_config
            stream_id = self.tester.pktgen.add_stream(txport, rxport, pkt)
            self.tester.pktgen.config_stream(stream_id, _option)
            stream_ids.append(stream_id)
        return stream_ids

    def __send_packets_by_pktgen(self, option):
        streams = option.get("stream")
        rate = option.get("rate")
        # set traffic option
        traffic_opt = option.get("traffic_opt")
        self.logger.debug(option)
        # clear streams before add new streams
        self.tester.pktgen.clear_streams()
        # set stream into pktgen
        stream_option = {
            "stream_config": {
                "txmode": {},
                "transmit_mode": TRANSMIT_CONT,
                "rate": rate,
            }
        }
        stream_ids = self.__add_stream_to_pktgen(streams, stream_option)
        # run packet generator
        result = self.tester.pktgen.measure(stream_ids, traffic_opt)
        self.logger.debug(
            f"wait {self.__traffic_stop_wait_time} second after traffic stop"
        )
        time.sleep(self.__traffic_stop_wait_time)
        return result

    def __throughput_set_traffic_opt(self, duration):
        option = {
            "method": "throughput",
            "duration": duration,
            "interval": self.__throughput_stat_sample_interval,
        }
        return option

    def __throughput_calculate_result(self, result):
        if self.__stat_algorithm is STAT_ALGORITHM.ONE:
            return result

        if not result or len(result) <= 0:
            msg = "failed to get throughput stat"
            self.logger.error(msg)
            return (0.0, 0.0)

        result = sorted(result)
        if self.__stat_algorithm is STAT_ALGORITHM.MEAN:
            result = result[1:-1] if len(result) >= 5 else result
            bps, pps = [], []
            for v1, v2 in result:
                bps.append(v1), pps.append(v2)
            ret_stat = round(np.array(bps).mean(), 1), round(np.array(pps).mean(), 1)
        else:
            msg = f"current not support algorithm <{self.__stat_algorithm}>"
            self.logger.warning(msg)
            ret_stat = (0.0, 0.0)

        return ret_stat

    def __throughput(self, l3_proto, mode, frame_size):
        """
        measure __throughput according to Layer-3 Protocol and Lookup Mode
        """
        flow_key = (l3_proto, mode, frame_size)
        if flow_key not in self.__streams.keys():
            msg = "{} {} {}: expected streams failed to create".format(*flow_key)
            raise VerifyFailure(msg)
        streams = self.__streams.get(flow_key)
        # set traffic option
        duration = self.__test_content.get("test_duration")
        option = {
            "stream": streams,
            "rate": 100,
            "traffic_opt": self.__throughput_set_traffic_opt(duration),
        }
        # run traffic
        result = self.__send_packets_by_pktgen(option)
        result = self.__throughput_calculate_result(result)
        # statistics result
        _, pps = result
        self.verify(pps > 0, "No traffic detected")
        return result

    def __rfc2544(self, config, l3_proto, mode, frame_size):
        """
        measure RFC2544 according to Layer-3 Protocol and Lookup Mode
        """
        flow_key = (l3_proto, mode, frame_size)
        if flow_key not in self.__streams.keys():
            msg = "{} {} {}: expected streams failed to create".format(*flow_key)
            raise VerifyFailure(msg)
        streams = self.__streams.get(flow_key)
        # set traffic option
        if not self.__cur_case:
            msg = "current test case name not set, use default traffic option"
            self.logger.warning(msg)
        conf_opt = (
            self.__test_content.get("expected_rfc2544", {})
            .get(self.__cur_case, {})
            .get(self.__nic_name, {})
            .get(config, {})
            .get(str(frame_size), {})
            .get("traffic_opt", {})
        )
        max_rate = float(conf_opt.get("max_rate") or 100.0)
        min_rate = float(conf_opt.get("min_rate") or 0.0)
        accuracy = float(conf_opt.get("accuracy") or 0.001)
        pdr = float(conf_opt.get("pdr") or 0.001)
        duration = self.__test_content.get("test_duration")
        option = {
            "stream": streams,
            "rate": max_rate,
            "traffic_opt": {
                "method": "rfc2544_dichotomy",
                "throughput_stat_flag": True,
                "max_rate": max_rate,
                "min_rate": min_rate,
                "accuracy": accuracy,
                "pdr": pdr,
                "duration": duration,
            },
        }
        # run traffic
        result = self.__send_packets_by_pktgen(option)
        # statistics result
        if result:
            _, tx_pkts, rx_pkts, _ = result
            self.verify(tx_pkts > 0, "No traffic detected")
            self.verify(rx_pkts > 0, "No packet transfer detected")
        else:
            msg = "failed to get zero loss rate percent with traffic option."
            self.logger.error(msg)
            self.logger.info(pformat(option))

        return result

    def __vf_init(self):
        self.__vf_ports_info = {}
        drvs = []
        if (
            self.__pf_driver is not NIC_DRV.PCI_STUB
            and self.__pf_driver.value != self.drivername
        ):
            drvs.append(self.__pf_driver.value)
        if self.__vf_driver.value != self.drivername:
            drvs.append(self.__vf_driver.value)
        for driver in drvs:
            self.dut.setup_modules(self.target, driver, "")

    def __vf_create(self):
        for index, port_id in enumerate(self.__valports):
            port_obj = self.dut.ports_info[port_id]["port"]
            pf_driver = (
                port_obj.default_driver
                if self.__pf_driver is NIC_DRV.PCI_STUB
                else self.__pf_driver.value
            )
            self.dut.generate_sriov_vfs_by_port(port_id, 1, driver=pf_driver)
            pf_pci = port_obj.pci
            sriov_vfs_port = self.dut.ports_info[port_id].get("vfs_port")
            if not sriov_vfs_port:
                msg = f"failed to create vf on dut port {pf_pci}"
                self.logger.error(msg)
                continue
            for port in sriov_vfs_port:
                port.bind_driver(driver=self.__vf_driver.value)
            vf_mac = "00:12:34:56:78:0%d" % (index + 1)
            self.__vf_ports_info[port_id] = {
                "pf_pci": pf_pci,
                "vfs_pci": port_obj.get_sriov_vfs_pci(),
                "vf_mac": vf_mac,
                "src_mac": "02:00:00:00:00:0%d" % index,
            }
            # ignore non pci stub
            if self.__pf_driver is not NIC_DRV.PCI_STUB:
                continue
            time.sleep(1)
            # set vf mac address.
            port_obj.set_vf_mac_addr(mac=vf_mac)
            pf_intf = port_obj.get_interface_name()
            cmd = f"ifconfig {pf_intf} up;" f"ethtool {pf_intf} | grep Speed"
            self.d_con(cmd)
        self.logger.debug(self.__vf_ports_info)

    def __vf_destroy(self):
        if not self.__vf_ports_info:
            return
        for port_id, _ in self.__vf_ports_info.items():
            self.dut.destroy_sriov_vfs_by_port(port_id)
            port_obj = self.dut.ports_info[port_id]["port"]
            port_obj.bind_driver(self.drivername)
        self.__vf_ports_info = None

    def __preset_dpdk_compilation(self):
        # rebuild to get best perf
        # RX_DESC
        rx_desc_comlication_flag = self.__get_rx_desc_complication_flag()
        if rx_desc_comlication_flag:
            self.dut.build_install_dpdk(
                self.target, extra_options=rx_desc_comlication_flag
            )

    def __restore_compilation(self):
        # restore build
        rx_desc_comlication_flag = self.__get_rx_desc_complication_flag()
        if rx_desc_comlication_flag:
            self.dut.build_install_dpdk(self.target)

    def __get_rx_desc_complication_flag(self):
        rx_desc_flag = ""
        if self.__compile_rx_desc:
            rx_desc_flag = f"-Dc_args=-DRTE_LIBRTE_{self.kdriver.upper()}_{self.__compile_rx_desc}BYTE_RX_DESC"
            if self.__compile_rx_desc == 32:
                msg = f"{rx_desc_flag} is dpdk default compile flag, ignore this compile flag"
                self.logger.warning(msg)
        return rx_desc_flag

    def __preset_compilation(self):
        # Update compile config file and rebuild to get best perf on different nics
        self.__preset_dpdk_compilation()
        if self.__mode is SUITE_TYPE.VF:
            # init testpmd
            if self.__pf_driver is not NIC_DRV.PCI_STUB:
                self.__init_host_testpmd()
        self.__l3fwd_init()

    def __init_host_testpmd(self):
        """
        apply under vf testing scenario
        """
        self.__pmd_session_name = "testpmd"
        self.__pmd_session = self.dut.create_session(self.__pmd_session_name)
        self.__host_testpmd = os.path.join(
            self.__target_dir, self.dut.apps_name["test-pmd"]
        )

    def __start_host_testpmd(self):
        """
        apply under vf testing scenario

        require enough PF ports,using kernel or dpdk driver, create 1 VF from each PF.
        """
        corelist = self.dut.get_core_list(
            "1S/{}C/1T".format(self.__core_offset), socket=self.__socket
        )
        core_mask = utils.create_mask(corelist[2:])
        # set memory size
        mem_size = ",".join(["1024"] * self.__sockets)
        cmd = (
            "{bin} "
            " -v "
            "-c {core_mask} "
            "-n {mem_channel} "
            "--socket-mem={memsize} "
            "--file-prefix={prefix} "
            "{allowlist} "
            "-- -i "
        ).format(
            **{
                "bin": self.__host_testpmd,
                "core_mask": core_mask,
                "mem_channel": self.dut.get_memory_channels(),
                "memsize": mem_size,
                "allowlist": self.__get_host_testpmd_allowlist(),
                "prefix": "pf",
            }
        )
        self.__host_pmd_con([cmd, "testpmd> ", 120])
        self.__is_pmd_on = True
        index = 0
        for _, info in self.__vf_ports_info.items():
            cmd = "set vf mac addr %d 0 %s" % (index, info.get("vf_mac"))
            self.__host_pmd_con([cmd, "testpmd> ", 15])
            index += 1
        self.__host_pmd_con(["start", "testpmd> ", 15])
        time.sleep(1)

    def __close_host_testpmd(self):
        """
        apply under vf testing scenario

        destroy the setup VFs
        """
        if not self.__is_pmd_on:
            return
        self.__host_pmd_con(["quit", "# ", 15])
        self.__is_pmd_on = False

    def __get_topo_option(self):
        port_num = (
            len(re.findall("-a", self.__bin_ps_allow_list))
            if self.__bin_ps_allow_list
            else len(self.__valports)
        )
        return "loop" if port_num == 1 else "chained"

    def __testpmd_start(self, mode, eal_para, config, frame_size):
        # use test pmd
        bin = os.path.join(self.__target_dir, self.dut.apps_name["test-pmd"])
        fwd_mode, _config = config
        port_topo = "--port-topology={}".format(self.__get_topo_option())
        command_line = (
            "{bin} "
            "-v "
            "{eal_para}"
            "-- -i "
            "--portmask {port_mask} "
            "{config} "
            "{port_topo} "
            ""
        ).format(
            **{
                "bin": bin,
                "eal_para": eal_para,
                "port_mask": utils.create_mask(self.__valports),
                "config": _config,
                "port_topo": port_topo,
            }
        )
        if self.__bin_ps_restart_check(command_line):
            return
        self.d_con([command_line, "testpmd>", 60])
        self.__is_bin_ps_on = True
        wait_time = (
            self.__bin_ps_wait_up if self.__bin_ps_wait_up else 2 * len(self.__valports)
        )
        self.logger.debug(f"wait {wait_time} seconds for port link up")
        time.sleep(wait_time)
        _cmds = [
            "set fwd {}".format(fwd_mode),
            "start",
        ]
        [self.dut.send_expect(cmd, "testpmd>") for cmd in _cmds]

    def __testpmd_close(self):
        if not self.__is_bin_ps_on:
            return
        if not self.__bin_ps_restart and self.__pre_bin_ps_cmd:
            return
        _cmds = [
            "show port stats all",
            "stop",
        ]
        [self.dut.send_expect(cmd, "testpmd>") for cmd in _cmds]
        self.dut.send_expect("quit", "# ")
        self.__is_bin_ps_on = False

    def __l3fwd_init(self):
        """
        compile l3fwd
        """
        self.app_name = self.dut.apps_name["l3fwd"].replace(" ", "")
        out = self.dut.build_dpdk_apps("./examples/l3fwd")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")
        self.__l3fwd_bin = os.path.join("./" + self.app_name)

    def __l3fwd_start(self, mode, eal_para, config, frame_size):
        # Start L3fwd application
        command_line = (
            "{bin} " "-v " "{eal_para}" "-- " "-p {port_mask} " "--config '{config}'" ""
        ).format(
            **{
                "bin": self.__l3fwd_bin,
                "eal_para": eal_para,
                "port_mask": utils.create_mask(self.__valports),
                "config": config,
            }
        )
        suppored_nics = [
            "IXGBE_10G-82599_SFP",
            "ICE_100G-E810C_QSFP",
            "ICE_25G-E810C_SFP",
            "ICE_25G-E810_XXV_SFP",
        ]
        if self.__rxtx_queue_size:
            command_line += " --rx-queue-size {rxtx} --tx-queue-size {rxtx}".format(
                rxtx=self.__rxtx_queue_size
            )
        if self.nic in suppored_nics or self.__mode is SUITE_TYPE.VF:
            command_line += " --parse-ptype"
        if mode == MATCH_MODE.EM:
            # use exact mode
            command_line += " -E"
        if frame_size > 1518:
            command_line += " --enable-jumbo --max-pkt-len %d" % frame_size
        # ignore duplicate start binary with the same option
        if self.__bin_ps_restart_check(command_line):
            return
        self.d_con([command_line, "L3FWD:", 120])
        self.__is_bin_ps_on = True
        # wait several second for l3fwd checking ports link status.
        # It is aimed to make sure packet generator detect link up status.
        wait_time = (
            self.__bin_ps_wait_up if self.__bin_ps_wait_up else 2 * len(self.__valports)
        )
        self.logger.debug(f"wait {wait_time} seconds for port link up")
        time.sleep(wait_time)

    def __l3fwd_close(self):
        if not self.__is_bin_ps_on:
            return
        if not self.__bin_ps_restart and self.__pre_bin_ps_cmd:
            return
        self.d_con(["^C", "# ", 25])
        self.__is_bin_ps_on = False

    def __bin_ps_start(self, mode, core_list, config, frame_size):
        eal_para = self.dut.create_eal_parameters(
            cores=core_list,
            ports=self.__bin_ps_allow_list,
            socket=self.__socket,
        )
        bin_methods = {
            BIN_TYPE.PMD: self.__testpmd_start,
            BIN_TYPE.L3FWD: self.__l3fwd_start,
        }
        start_func = bin_methods.get(self.__bin_type)
        start_func(mode, eal_para, config, frame_size)

    def __bin_ps_close(self):
        bin_methods = {
            BIN_TYPE.PMD: self.__testpmd_close,
            BIN_TYPE.L3FWD: self.__l3fwd_close,
        }
        close_func = bin_methods.get(self.__bin_type)
        close_func()

    def __bin_ps_restart_check(self, command_line):
        if self.__bin_ps_restart:
            self.__pre_bin_ps_cmd = None
            return False

        if self.__pre_bin_ps_cmd and self.__pre_bin_ps_cmd == command_line:
            self.logger.debug(
                (
                    f"<{command_line}> is the same command as previous one, "
                    f"ignore re-start {self.__bin_type.value}"
                )
            )
            return True
        else:
            self.__pre_bin_ps_cmd = None
            self.__bin_ps_close()
            self.__pre_bin_ps_cmd = command_line
            return False

    def __json_rfc2544(self, value):
        return {
            "unit": "Mpps",
            "name": "Rfc2544",
            "value": round(value[0], 3),
            "delta": round(value[1], 3),
            "Expected Throughput": round(value[2], 3),
        }

    def __json_throughput(self, value):
        return {
            "unit": "Mpps",
            "name": "Throughput",
            "value": round(value[0], 3),
            "delta": value[1],
            "expected": value[2],
        }

    def __json_rate_percent(self, value):
        return {"unit": "", "name": "% of Line Rate", "value": round(value, 3)}

    def __json_port_config(self, value):
        return {"unit": "", "name": "Number of Cores/Threads/Queues", "value": value}

    def __json_frame_size(self, value):
        return {"unit": "bytes", "name": "Frame size", "value": value}

    def __save_throughput_result(self, case_name, result):
        case_result = []
        for sub_result in result:
            status, throughput, rate_percent, port_config, frame_size = sub_result
            one_result = {
                "status": status,
                "performance": [
                    self.__json_throughput(throughput),
                    self.__json_rate_percent(rate_percent),
                ],
                "parameters": [
                    self.__json_port_config(port_config),
                    self.__json_frame_size(frame_size),
                ],
            }
            case_result.append(one_result)
        self.logger.debug(pformat(case_result))
        self.__json_results[case_name] = case_result

    def __save_rfc2544_result(self, case_name, result):
        case_result = []
        for sub_result in result:
            status, rfc2544, rate_percent, port_config, frame_size = sub_result
            one_result = {
                "status": status,
                "performance": [
                    self.__json_rfc2544(rfc2544),
                    self.__json_rate_percent(rate_percent),
                ],
                "parameters": [
                    self.__json_port_config(port_config),
                    self.__json_frame_size(frame_size),
                ],
            }
            case_result.append(one_result)
        self.logger.debug(pformat(case_result))
        self.__json_results[case_name] = case_result

    def l3fwd_save_results(self, json_file=None):
        _json_file = json_file if json_file else "l3fwd_result.json"
        self.perf_test_save_results(_json_file)

    def perf_test_save_results(self, json_file=None):
        if not self.__json_results:
            msg = "json results data is empty"
            self.logger.error(msg)
            return
        _js_file = os.path.join(
            self.__output_path,
            json_file if json_file else f"{self.suite_name}_result.json",
        )
        with open(_js_file, "w") as fp:
            json.dump(
                self.__json_results,
                fp,
                indent=4,
                separators=(",", ": "),
                sort_keys=True,
            )

    def __display_mode_name(self, mode):
        if self.__bin_type is BIN_TYPE.PMD:
            mode_name = "L3 fixed" if mode is MATCH_MODE.EM else "L3 random"
        else:
            mode_name = mode.value
        return mode_name

    def __display_suite_result(self, data):
        from texttable import Texttable

        values = data.get("values")
        title = data.get("title")
        max_length = sum([len(item) + 5 for item in title])
        self.result_table_create(title)
        self._result_table.table = Texttable(max_width=max_length)
        for value in values:
            self.result_table_add(value)
        self.result_table_print()

    def __check_throughput_result(self, stm_name, data, mode):
        if not data:
            msg = "no result data"
            raise VerifyFailure(msg)
        values = []
        js_results = []
        bias = float(self.__test_content.get("accepted_tolerance") or 1.0)
        for sub_data in data:
            config, frame_size, result = sub_data
            _, pps = result
            pps /= 1000000.0
            _frame_size = self.__get_frame_size(stm_name, frame_size)
            linerate = self.wirespeed(self.nic, _frame_size, len(self.__valports))
            percentage = pps * 100 / linerate
            # data for display
            values.append([config, frame_size, mode.upper(), str(pps), str(percentage)])
            # check data with expected values
            expected_rate = (
                None
                if not self.__cur_case
                else self.__test_content.get("expected_throughput", {})
                .get(self.__cur_case, {})
                .get(self.__nic_name, {})
                .get(config, {})
                .get(str(frame_size))
            )
            if expected_rate and float(expected_rate):
                expected = float(expected_rate)
                gap = 100 * (pps - expected) / expected
                if abs(gap) < bias:
                    status = "pass"
                else:
                    status = "failed"
                    msg = (
                        "expected <{}>, "
                        "current <{}> is "
                        "{}% over accepted tolerance"
                    ).format(expected, pps, round(gap, 2))
                    self.logger.error(msg)
            else:
                expected = None
                msg = (
                    "{0} {1} expected throughput value is not set, " "ignore check"
                ).format(config, frame_size)
                self.logger.warning(msg)
                status = "pass"
            js_results.append(
                [
                    status,
                    [
                        pps,
                        (str(round((pps - expected) / expected, 3)))
                        if expected is not None
                        else "N/A",
                        round(expected, 3) if expected is not None else "N/A",
                    ],
                    percentage,
                    config,
                    frame_size,
                ]
            )
        # save data with json format
        self.__save_throughput_result(self.__cur_case, js_results)
        # display result table
        title = [
            "Total Cores/Threads/Queues per port",
            "Frame Size",
            "Mode",
            "Throughput Rate {} Mode mpps".format(mode.upper()),
            "Throughput Rate {} Mode Linerate%".format(mode.upper()),
        ]

        _data = {"title": title, "values": values}
        self.__display_suite_result(_data)

    def __check_rfc2544_result(self, stm_name, data, mode):
        if not data:
            msg = "no result data"
            raise Exception(msg)
        bias = self.__test_content.get("accepted_tolerance")
        values = []
        js_results = []
        for sub_data in data:
            config, frame_size, result = sub_data
            expected_cfg = (
                {}
                if not self.__cur_case
                else self.__test_content.get("expected_rfc2544", {})
                .get(self.__cur_case, {})
                .get(self.__nic_name, {})
                .get(config, {})
                .get(str(frame_size), {})
            )
            zero_loss_rate, tx_pkts, rx_pkts, pps = result if result else [None] * 4
            zero_loss_rate = zero_loss_rate or 0
            mpps = pps / 1000000.0
            # expected line rate
            _frame_size = self.__get_frame_size(stm_name, frame_size)
            linerate = self.wirespeed(self.nic, _frame_size, len(self.__valports))
            actual_rate_percent = mpps * 100 / linerate
            # append data for display
            pdr = expected_cfg.get("traffic_opt", {}).get("pdr")
            expected_rate = float(expected_cfg.get("rate") or 100.0)
            values.append(
                [
                    config,
                    frame_size,
                    mode.upper(),
                    str(linerate * expected_rate / 100),
                    str(mpps),
                    str(expected_rate),
                    str(actual_rate_percent),
                    str(tx_pkts),
                    str(rx_pkts),
                ]
            )
            # check data with expected values
            gap = 100 * (actual_rate_percent - expected_rate) / expected_rate
            status = "pass" if abs(gap) < bias else "failed"
            js_results.append(
                [
                    status,
                    [mpps, actual_rate_percent - expected_rate, linerate],
                    actual_rate_percent,
                    config,
                    frame_size,
                ]
            )
        # save data in json file
        self.__save_rfc2544_result(self.__cur_case, js_results)
        # display result table
        # Total Cores/Threads/Queues per port
        # Frame Size
        # Mode: LPM/EM
        # Expected Throughput (Mpps)  :  Max linerate throughput value *  'Expected LineRate %'
        # Actual Throughput (Mpps)  :  actual run throughput value on the zero loss rate
        # Expected LineRate %  :  which config in <suite name>.cfg
        # Actual LineRate %  :  actual run zero loss rate
        # tx_pkts :  send pkts num
        # rx_pkts :  received pkts num
        title = [
            "Total Cores/Threads/Queues per port",
            "Frame Size",
            "Mode",
            "Expected Throughput (Mpps)",
            "Actual Throughput (Mpps) ",
            "{} Mode config line rate % ".format(mode.upper()),
            "{} Mode actual line rate % ".format(mode.upper()),
            "tx_pkts",
            "rx_pkts",
        ]

        _data = {"title": title, "values": values}
        self.__display_suite_result(_data)

    def ms_throughput(self, l3_proto, mode):
        except_content = None
        try:
            test_content = self.__test_content.get("port_configs")
            results = []
            for config, core_list, port_conf, frame_size in test_content:
                # Start application binary process
                self.logger.info(
                    (
                        "Executing {4} with {0} mode, {1} ports, "
                        "{2} and {3} frame size"
                    ).format(
                        self.__display_mode_name(mode),
                        len(self.__valports),
                        config,
                        frame_size,
                        self.__bin_type.value,
                    )
                )
                self.__bin_ps_start(mode, core_list, port_conf, frame_size)
                result = self.__throughput(l3_proto, mode, frame_size)
                # Stop binary process
                self.__bin_ps_close()
                if result:
                    results.append([config, frame_size, result])
            self.__check_throughput_result(
                l3_proto, results, self.__display_mode_name(mode)
            )
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.__pre_bin_ps_cmd = None
            self.__bin_ps_close()

        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def qt_rfc2544(self, l3_proto, mode):
        except_content = None
        try:
            test_content = self.__test_content.get("port_configs")
            results = []
            for config, core_list, port_conf, frame_size in test_content:
                # Start application binary process
                self.logger.info(
                    (
                        "Executing {4} with {0} mode, {1} ports, "
                        "{2} and {3} frame size"
                    ).format(
                        self.__display_mode_name(mode),
                        len(self.__valports),
                        config,
                        frame_size,
                        self.__bin_type.value,
                    )
                )
                self.__bin_ps_start(mode, core_list, port_conf, frame_size)
                result = self.__rfc2544(config, l3_proto, mode, frame_size)
                # Stop binary process
                self.__bin_ps_close()
                if result:
                    results.append([config, frame_size, result])
            self.__check_rfc2544_result(
                l3_proto, results, self.__display_mode_name(mode)
            )
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.__pre_bin_ps_cmd = None
            self.__bin_ps_close()

        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def __parse_port_config(self, config, cores_for_all):
        """
        [n]C/[mT]-[i]Q

            n: how many physical core use for polling.
            m: how many cpu thread use for polling, if Hyper-threading disabled
                in BIOS, m equals n, if enabled, m is 2 times as n.
            i: how many queues use per port, so total queues = i x nb_port
        """
        # old format
        pat = "(.*)\/(.*)\/(.*)"
        result1 = re.findall(pat, config)
        # new format
        pat = "(.*)\/(.*)-(.*)"
        result2 = re.findall(pat, config)
        result = result1 if result1 else result2
        if not result:
            msg = f"{config} is wrong format, please check"
            raise VerifyFailure(msg)
        cores, total_threads, queue = result[0]
        _thread_num = int(int(total_threads[:-1]) // int(cores[:-1]))
        _thread_num = (
            self.__core_thread_num
            if _thread_num > self.__core_thread_num
            else _thread_num
        )
        _thread = str(_thread_num) + "T"
        multiple = 1 if cores_for_all else len(self.__valports)
        _cores = str(self.__core_offset + int(cores[:-1]) * multiple) + "C"
        if len(self.__valports) == 1 and int(total_threads[:-1]) > int(
            queue[:-1]
        ) * len(self.__valports):
            msg = f"Invalid configuration: {config}, please check"
            self.logger.warning(msg)
        if int(total_threads[:-1]) not in [
            self.__core_thread_num * int(cores[:-1]),
            int(cores[:-1]),
        ]:
            support_num = (
                f"1 or {self.__core_thread_num}" if self.__core_thread_num > 1 else "1"
            )
            msg = (
                f"Invalid configuration: {config}, "
                f"threads should be {support_num} times of cores"
            )
            self.logger.warning(msg)
        # only use one socket
        cores_config = "/".join(["1S", _cores, _thread])
        queues_per_port = int(queue[:-1])
        return cores_config, _thread_num, queues_per_port

    def __get_core_list(self, thread_num, cores, socket):
        corelist = self.dut.get_core_list(
            cores, socket if cores.startswith("1S") else -1
        )
        if self.__bin_type is BIN_TYPE.PMD:
            corelist = corelist[(self.__core_offset - 1) * thread_num :]
        else:
            corelist = corelist[self.__core_offset * thread_num :]
        if "2T" in cores:
            corelist = corelist[0::2] + corelist[1::2]
        return corelist

    def __get_test_configs(
        self, options, ports, socket, cores_for_all, fixed_config=None
    ):
        if not options:
            msg = "'test_parameters' not set in suite configuration file"
            raise VerifyFailure(msg)
        configs = []
        frame_sizes_grp = []
        for test_item, frame_sizes in sorted(options.items()):
            _frame_sizes = [int(frame_size) for frame_size in frame_sizes]
            frame_sizes_grp.extend([int(item) for item in _frame_sizes])
            cores, thread_num, queues_per_port = self.__parse_port_config(
                test_item, cores_for_all
            )
            grp = [list(item) for item in product(range(ports), range(queues_per_port))]
            corelist = self.__get_core_list(thread_num, cores, socket)

            if self.__bin_type == BIN_TYPE.PMD:
                # keep only one logic core of the main core
                _corelist = corelist[thread_num - 1 :]
                [
                    configs.append(
                        [
                            test_item,
                            _corelist,
                            [
                                fixed_config[0],
                                fixed_config[1]
                                + " --rxq={0} --txq={0}".format(queues_per_port)
                                + " --nb-cores={}".format(len(corelist) - thread_num),
                            ],
                            frame_size,
                        ]
                    )
                    for frame_size in _frame_sizes
                ]
            # (port,queue,lcore)
            else:
                total = len(grp)
                # ignore first 2 cores
                _corelist = (corelist * (total // len(corelist) + 1))[:total]
                [grp[index].append(core) for index, core in enumerate(_corelist)]
                [
                    configs.append(
                        [
                            test_item,
                            _corelist,
                            ",".join(
                                [
                                    "({0},{1},{2})".format(port, queue, core)
                                    for port, queue, core in grp
                                ]
                            ),
                            frame_size,
                        ]
                    )
                    for frame_size in _frame_sizes
                ]
        return configs, sorted(set(frame_sizes_grp))

    def __get_suite_vf_pf_driver(self, test_content):
        if self.__suite is SUITE_NAME.VF_KERNELPF:
            pf_driver = NIC_DRV.PCI_STUB.value
            vf_driver = None  # used configuration in execution.cfg
        else:  # use config in <suite name>.cfg
            pf_driver = test_content.get("pf_driver")
            vf_driver = test_content.get("vf_driver")
        return pf_driver, vf_driver

    def __set_suite_series_name(self):
        pat = "vf_l3fwd.*_kernelpf"
        if re.match(pat, self.suite_name):
            self.__suite = SUITE_NAME.VF_KERNELPF
            return
        pat = "testpmd*_perf"
        if re.match(pat, self.suite_name):
            self.__suite = SUITE_NAME.TESTPMD_PERF
            return
        self.__suite = None

    def __get_vf_test_content_from_cfg(self, test_content):
        self.__set_suite_series_name()
        # pf driver
        pf_driver, vf_driver = self.__get_suite_vf_pf_driver(test_content)
        if pf_driver and isinstance(pf_driver, str):
            self.__pf_driver = get_enum_name(pf_driver.lower(), NIC_DRV)
        else:
            self.__pf_driver = get_enum_name(self.drivername.lower(), NIC_DRV)
            msg = (
                f"pf driver use {self.__pf_driver}, " f"{pf_driver} is set in cfg file"
            )
            self.logger.warning(msg)
        # limit pf driver usage
        if self.__pf_driver is NIC_DRV.IGB_UIO or self.__pf_driver is NIC_DRV.PCI_STUB:
            pass
        else:
            msg = f"not support {self.__pf_driver.value} for pf nic !"
            raise VerifyFailure(msg)
        # vf driver
        if (
            vf_driver
            and isinstance(vf_driver, str)
            and vf_driver != NIC_DRV.PCI_STUB.value
        ):
            self.__vf_driver = get_enum_name(vf_driver.lower(), NIC_DRV)
        else:
            self.__vf_driver = get_enum_name(self.drivername.lower(), NIC_DRV)
            msg = (
                f"vf driver use {self.__vf_driver}, " f"{vf_driver} is set in cfg file"
            )
            self.logger.warning(msg)
        # limit vf driver usage
        if self.__vf_driver is NIC_DRV.IGB_UIO or self.__vf_driver is NIC_DRV.VFIO_PCI:
            pass
        else:
            msg = f"not support {self.__vf_driver.value} for vf nic !"
            raise VerifyFailure(msg)
        # set core offset
        self.logger.info(
            f"pf driver type: {self.__pf_driver}, "
            f"vf driver type: {self.__vf_driver}"
        )
        if self.__pf_driver is not NIC_DRV.PCI_STUB:
            self.__core_offset += max(2, len(self.__valports))

    def __get_test_content_from_cfg(self, test_content):
        self.logger.debug(pformat(test_content))
        # get flows configuration
        conf_table = {
            SUITE_TYPE.PF: "l3fwd_base",
            SUITE_TYPE.VF: "vf_l3fwd_base",
        }
        conf_name = conf_table.get(self.__mode)
        if not conf_name:
            msg = f"{self.__mode} not supported"
            raise VerifyFailure(msg)
        suite_conf = SuiteConf(conf_name)
        flows = suite_conf.suite_cfg.get("l3fwd_flows")
        test_content["flows"] = flows
        # set stream format type
        stream_type = suite_conf.suite_cfg.get("stream_type")
        if stream_type and isinstance(stream_type, str):
            self.__pkt_typ = get_enum_name(stream_type.upper(), STREAM_TYPE)
        else:
            msg = f"use default stream format {self.__pkt_typ.value}"
            self.logger.warning(msg)
        # get vf driver
        if self.__mode is SUITE_TYPE.VF:
            self.__get_vf_test_content_from_cfg(test_content)
        # binary file process setting
        if self.__bin_type is BIN_TYPE.L3FWD:
            self.__bin_ps_wait_up = test_content.get("l3fwd_wait_up", 0)
            self.__bin_ps_restart = test_content.get("l3fwd_restart", True)
            self.__rxtx_queue_size = test_content.get("rxtx_queue_size", None)
        else:
            self.__bin_ps_wait_up = test_content.get("bin_ps_wait_up", 0)
            self.__bin_ps_restart = test_content.get("bin_ps_restart", True)
        self.__traffic_stop_wait_time = test_content.get("traffic_stop_wait_time", 0)
        # parse port config of binary process suite
        cores_for_all = test_content.get("cores_for_all", False)
        self.__compile_rx_desc = test_content.get("compile_rx_desc")
        if self.__bin_type == BIN_TYPE.PMD:
            forwarding_mode = test_content.get("forwarding_mode") or "io"
            descriptor_numbers = test_content.get("descriptor_numbers") or {
                "txd": 2048,
                "rxd": 2048,
            }
            fixed_config = [
                forwarding_mode,
                "--rxd={rxd} --txd={txd}".format(**descriptor_numbers),
            ]
            self.__core_offset += 1
        else:
            fixed_config = None
        port_configs, frame_sizes = self.__get_test_configs(
            test_content.get("test_parameters"),
            len(self.__valports),
            self.__socket,
            cores_for_all,
            fixed_config=fixed_config,
        )
        test_content["port_configs"] = port_configs
        test_content["frame_sizes"] = frame_sizes
        self.logger.debug(pformat(test_content))

        return test_content

    def __get_bin_ps_allowlist(self, port_list=None):
        allowlist = []
        if self.__mode is SUITE_TYPE.PF:
            if not port_list:
                return None
            for port_index in port_list:
                pci = self.dut.ports_info[port_index].get("pci")
                if not pci:
                    continue
                allowlist.append(pci)
        else:
            for _, info in self.__vf_ports_info.items():
                for pci in info.get("vfs_pci"):
                    allowlist.append(pci)

        return allowlist

    def __get_host_testpmd_allowlist(self):
        allowlist = "".join(
            [
                "-a {} ".format(info.get("pf_pci"))
                for _, info in self.__vf_ports_info.items()
            ]
        )
        return allowlist

    def __preset_port_list(self, test_content):
        port_list = test_content.get("port_list")
        if port_list:
            if not set(port_list).issubset(set(self.__valports)):
                msg = "total ports are {}, select ports are wrong".format(
                    pformat(self.__valports)
                )
                raise VerifyFailure(msg)
            else:
                msg = "current using ports {} for testing".format(pformat(port_list))
                self.logger.info(msg)
            self.__valports = port_list
        return port_list

    @property
    def __stat_algorithm(self):
        algorithm_type = get_enum_name(
            self.__test_content.get("stat_algorithm") or "one", STAT_ALGORITHM
        )
        return algorithm_type

    @property
    def __throughput_stat_sample_interval(self):
        if self.__stat_algorithm is STAT_ALGORITHM.ONE:
            return None
        else:
            return self.__test_content.get("throughput_stat_sample_interval") or 5

    def __parse_accepted_tolerance(self):
        tolerance = self.__test_content.get("accepted_tolerance")

        def get_num(value):
            pat = "(\d+\.?\d?)"
            result = re.findall(pat, value)
            return result[0] if result else "2.0"

        if isinstance(tolerance, int):
            _tolerance = float(tolerance)
        elif isinstance(tolerance, str):
            _tolerance = float(tolerance if tolerance.isdigit() else get_num(tolerance))
        else:
            _tolerance = None
        self.__test_content["accepted_tolerance"] = float(_tolerance or 2.0)

    def perf_preset_test_environment(self, test_content):
        # if user set port list in cfg file, use
        port_list = self.__preset_port_list(test_content)
        # get test content
        self.__test_content = self.__get_test_content_from_cfg(test_content)
        self.__parse_accepted_tolerance()
        # prepare target source code application
        self.__preset_compilation()
        # set up testing environment
        if self.__mode is SUITE_TYPE.VF:
            self.__vf_init()
            self.__vf_create()
            self.__bin_ps_allow_list = self.__get_bin_ps_allowlist()
            if self.__pf_driver is not NIC_DRV.PCI_STUB:
                self.__start_host_testpmd()
        else:
            self.__bin_ps_allow_list = self.__get_bin_ps_allowlist(port_list)
        # config streams
        self.__streams = self.__preset_streams()

    def perf_destroy_resource(self):
        if self.__mode is SUITE_TYPE.VF:
            if self.__pf_driver is NIC_DRV.PCI_STUB:
                pass
            else:
                self.__close_host_testpmd()
                if self.__pmd_session:
                    self.dut.close_session(self.__pmd_session)
                    self.__pmd_session = None
            self.__vf_destroy()
        self.__restore_compilation()

    def perf_set_cur_case(self, name):
        self.__cur_case = name

    def perf_reset_cur_case(self):
        self.__cur_case = None

    @property
    def is_pktgen_on(self):
        return hasattr(self.tester, "is_pktgen") and self.tester.is_pktgen

    @property
    def pktgen_type(self):
        if self.is_pktgen_on:
            return self.tester.pktgen.pktgen_type
        else:
            return "scapy"

    def verify_ports_number(self, port_num):
        supported_num = {
            PKTGEN_TREX: [2, 4],
            PKTGEN_IXIA: [1, 2, 4],
            PKTGEN_IXIA_NETWORK: [1, 2, 4],
        }
        if not self.is_pktgen_on:
            msg = "not using pktgen"
            self.logger.warning(msg)
            return
        # verify that enough ports are available
        _supported_num = supported_num.get(self.pktgen_type)
        msg = "Port number must be {} when using pktgen <{}>".format(
            pformat(_supported_num), self.pktgen_type
        )
        self.verify(len(port_num) in _supported_num, msg)
