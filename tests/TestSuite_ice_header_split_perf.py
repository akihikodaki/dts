# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

"""
DPDK Test suite.
"""

import os
import re
import time
from copy import deepcopy

import framework.utils as utils
from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.pktgen import TRANSMIT_CONT
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase
from framework.utils import convert_int2ip, convert_ip2int


class TestICEHeaderSplitPerf(TestCase):
    #
    # Test cases.
    #
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.verify(
            self.nic
            in ["ICE_100G-E810C_QSFP", "ICE_25G-E810C_SFP", "ICE_25G-E810_XXV_SFP"],
            "NIC Unsupported: " + str(self.nic),
        )
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "At least 1 port is required to test")
        # Get socket and cores
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        cores = self.dut.get_core_list("1S/8C/1T", socket=self.socket)
        self.verify(cores, "Requested 8 cores failed")
        self.core_offset = 3
        self.test_content = self.get_test_content_from_cfg(self.get_suite_cfg())

    def set_up(self):
        """
        Run before each test case.
        """
        self.test_result = {"header": [], "data": []}

    def flows(self):
        """
        Return a list of packets that implements the flows described.
        """
        return [
            "198.18.0.0/24",
            "198.18.1.0/24",
            "198.18.2.0/24",
            "198.18.3.0/24",
            "198.18.4.0/24",
            "198.18.5.0/24",
            "198.18.6.0/24",
            "198.18.7.0/24",
        ]

    def parse_test_config(self, config):
        """
        [n]C/[mT]-[i]Q
            n: how many physical core use for polling.
            m: how many cpu thread use for polling, if Hyper-threading disabled
            in BIOS, m equals n, if enabled, m is 2 times as n.
            i: how many queues use per port, so total queues = i x nb_port
        """
        pat = "(.*)/(.*)-(.*)"
        result = re.findall(pat, config)
        if not result:
            msg = f"{config} is wrong format, please check"
            raise VerifyFailure(msg)
        cores, threads, queue = result[0]
        _thread_num = int(int(threads[:-1]) // int(cores[:-1]))

        _thread = str(_thread_num) + "T"
        _cores = str(self.core_offset + int(cores[:-1])) + "C"
        cores_config = "/".join(["1S", _cores, _thread])
        queues_per_port = int(queue[:-1])
        return cores_config, _thread_num, queues_per_port

    def get_test_configs(self, test_parameters):
        configs = []
        frame_sizes_grp = []
        for test_item, frame_sizes in sorted(test_parameters.items()):
            _frame_sizes = [int(frame_size) for frame_size in frame_sizes]
            frame_sizes_grp.extend([int(item) for item in _frame_sizes])
            cores, thread_num, queues = self.parse_test_config(test_item)
            corelist = self.dut.get_core_list(cores, self.socket)
            core_list = corelist[(self.core_offset - 1) * thread_num :]
            if "2T" in cores:
                core_list = core_list[1:2] + core_list[0::2] + core_list[1::2][1:]
            _core_list = core_list[thread_num - 1 :]
            configs.append(
                [
                    test_item,
                    _core_list,
                    [
                        " --txd=1024 --rxd=1024"
                        + " --rxq={0} --txq={0}".format(queues)
                        + " --nb-cores={}".format(len(core_list) - thread_num)
                    ],
                ]
            )
        return configs, sorted(set(frame_sizes_grp))

    def get_test_content_from_cfg(self, test_content):
        test_content["flows"] = self.flows()
        configs, frame_sizes = self.get_test_configs(test_content["test_parameters"])
        test_content["configs"] = configs
        test_content["frame_sizes"] = frame_sizes
        return test_content

    def get_mac_layer(self, port_id):
        smac = "02:00:00:00:00:0%d" % port_id
        dmac = "52:00:00:00:00:0%d" % port_id

        layer = {
            "ether": {
                "dst": dmac,
                "src": smac,
            },
        }
        return layer

    def get_ipv4_config(self, config):
        netaddr, mask = config.split("/")
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

    def preset_flows_configs(self):
        flows = self.test_content.get("flows")
        flows_configs = []
        for index, config in enumerate(flows):
            if index >= len(self.dut_ports):
                break
            port_id = self.dut_ports[index]
            _layer = self.get_mac_layer(port_id)
            _layer2, fields_config = self.get_ipv4_config(config)
            _layer.update(_layer2)
            flows_configs.append([_layer, fields_config])
        return flows_configs

    def preset_streams(self, pkt_type):
        frame_sizes = self.test_content.get("frame_sizes")
        test_streams = {}
        frame_sizes_new = []
        flows_configs = self.preset_flows_configs()
        for frame_size in frame_sizes:
            frame_size = 66 if "udp" == pkt_type and frame_size == 64 else frame_size
            frame_sizes_new.append(frame_size)
            for flow_config in flows_configs:
                _layers, fields_config = flow_config
                pkt = self.config_stream(_layers, frame_size, pkt_type)
                test_streams.setdefault(frame_size, []).append([pkt, fields_config])
        return test_streams, frame_sizes_new

    def config_stream(self, layers, frame_size, pkt_mode):
        """
        Prepare traffic flow
        """
        if pkt_mode == "udp":
            headers_size = sum([HEADER_SIZE[x] for x in ["eth", "ip", "udp"]])
            payload_size = frame_size - headers_size
            pkt_config = {
                "type": "UDP",
                "pkt_layers": {"raw": {"payload": ["58"] * payload_size}},
            }
            layers["udp"] = {"src": 53, "dst": 53}
        else:
            headers_size = sum([HEADER_SIZE[x] for x in ["eth", "ip"]])
            payload_size = frame_size - headers_size
            # Set streams for traffic
            pkt_config = {
                "type": "IP_RAW",
                "pkt_layers": {"raw": {"payload": ["58"] * payload_size}},
            }
        pkt_config["pkt_layers"].update(layers)
        pkt_type = pkt_config.get("type")
        pkt_layers = pkt_config.get("pkt_layers")
        pkt = Packet(pkt_type=pkt_type)
        for layer in list(pkt_layers.keys()):
            pkt.config_layer(layer, pkt_layers[layer])

        return pkt.pktgen.pkt

    def add_stream_to_pktgen(self, streams, option):
        def port(index):
            p = self.tester.get_local_port(self.dut_ports[index])
            return p

        topos = (
            [
                [port(index), port(index - 1)]
                if index % 2
                else [port(index), port(index + 1)]
                for index, _ in enumerate(self.dut_ports)
            ]
            if len(self.dut_ports) > 1
            else [[port(0), port(0)]]
        )
        stream_ids = []
        step = int(len(streams) / len(self.dut_ports))
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

    def start_testpmd(self, eal_pare, eal):
        bin = os.path.join(self.dut.base_dir, self.dut.apps_name["test-pmd"])
        command_line = (
            "{bin} "
            "{eal_para}"
            " --force-max-simd-bitwidth=64 "
            "-- -i "
            "--portmask {port_mask} "
            "{config} "
            ""
        ).format(
            **{
                "bin": bin,
                "eal_para": eal_pare,
                "port_mask": utils.create_mask(self.dut_ports),
                "config": eal,
            }
        )
        self.dut.send_expect(command_line, "testpmd>", 60)

    def throughput(self, frame_size, fwd_mode):
        streams = self.stream.get(frame_size)
        # Set traffic option
        duration = self.test_content.get("test_duration")
        traffic_stop_wait_time = self.test_content.get("traffic_stop_wait_time", 0)
        # Clear streams before adding new streams
        self.tester.pktgen.clear_streams()
        # Set stream into pktgen
        stream_option = {
            "stream_config": {
                "txmode": {},
                "transmit_mode": TRANSMIT_CONT,
                "rate": 100,
            }
        }
        traffic_option = {
            "method": "throughput",
            "duration": duration,
        }
        stream_ids = self.add_stream_to_pktgen(streams, stream_option)
        # Run packet generator
        result = self.tester.pktgen.measure(stream_ids, traffic_option)
        time.sleep(traffic_stop_wait_time)
        # Statistics result
        if fwd_mode == "rxonly":
            # Calculate rx throughput
            out = self.dut.send_expect("show port stats all", "testpmd> ", 15)
            pattern = re.compile(r"(?<=RX-packets: )\d+\.?\d*")
            pps = int(pattern.findall(out)[0]) / duration
        else:
            _, pps = result
        self.verify(pps > 0, "No traffic detected")
        self.logger.info(
            "Throughput of "
            + "framesize: {}, is: {} Mpps".format(frame_size, pps / 1000000)
        )
        return pps

    def get_port_allowlist(self, port_list=None):
        allowlist = []
        if port_list:
            for port_id in port_list:
                pci = self.dut.ports_info[port_id]["port"].pci
                allowlist.append(pci)
        return allowlist

    def display_result(self, datas):
        # Display result table
        header_row = ["Fwd Core", "Frame Size", "Throughput", "Rate"]
        self.test_result["header"] = header_row
        self.result_table_create(header_row)
        self.test_result["data"] = []
        for data in datas:
            config, frame_size, pps = data
            pps /= 1000000.0
            linerate = self.wirespeed(self.nic, frame_size, len(self.dut_ports))
            percentage = pps * 100 / linerate
            data_row = [
                config,
                frame_size,
                "{:.3f} Mpps".format(pps),
                "{:.3f}%".format(percentage),
            ]
            self.result_table_add(data_row)
            self.test_result["data"].append(data_row)
        self.result_table_print()

    def config_header_split(self, split_type):
        self.dut.send_expect("port stop all", "testpmd> ", 15)
        for i in self.dut_ports:
            self.dut.send_expect(
                "port config {} rx_offload buffer_split on".format(i), "testpmd> ", 15
            )
        if split_type == "eth":
            self.dut.send_expect("set rxhdrs eth", "testpmd> ", 15)
        elif split_type == "udp":
            self.dut.send_expect("set rxhdrs inner-ipv4-udp", "testpmd> ", 15)
        self.dut.send_expect("port start all", "testpmd> ", 15)
        self.check_port_stats()

    def check_port_stats(self, times=60):
        # Check port status up
        for i in range(times):
            out = self.dut.send_expect("show port info all", "testpmd> ")
            pattern = r"(?<=%s)%s" % ("Link status: ", "\S+")
            s = re.compile(pattern)
            status = s.findall(out)
            if "down" not in status:
                break
            time.sleep(1)

    def perf_test(self, fwd_mode="", mbuf_size="", header_split="", pkt_type=""):
        """
        Benchmarking test
        """
        self.stream, self.frame_sizes = self.preset_streams(pkt_type)
        # Ports allow list
        port_allowlist = self.get_port_allowlist(self.dut_ports)
        forward = " --forward={}".format(fwd_mode)
        results = []
        for config, core_list, eal in self.test_content["configs"]:
            self.logger.info(
                ("Executing Test Using cores: {0} of config {1}, ").format(
                    core_list, config
                )
            )
            eal_pare = self.dut.create_eal_parameters(
                cores=core_list, ports=port_allowlist, socket=self.socket
            )
            eal = eal[0] + forward
            if "enable" == mbuf_size:
                eal += " --mbuf-size=2048,2048"
            self.start_testpmd(eal_pare, eal)
            self.check_port_stats()
            if header_split:
                self.config_header_split(header_split)
            self.dut.send_expect("start", "testpmd> ", 15)
            for frame_size in self.frame_sizes:
                self.logger.info("Test running at framesize: {}".format(frame_size))
                self.dut.send_expect("clear port stats all", "testpmd> ", 15)
                result = self.throughput(frame_size, fwd_mode)
                if result:
                    results.append([config, frame_size, result])
            self.dut.send_expect("stop", "testpmd> ", 15)
            self.dut.send_expect("quit", "# ", 15)
        self.display_result(results)

    def test_perf_enable_header_split_rx_on(self):
        self.perf_test(fwd_mode="rxonly", mbuf_size="enable", header_split="eth")

    def test_perf_disable_header_split_rx_on(self):
        self.perf_test(fwd_mode="rxonly")
        self.perf_test(fwd_mode="rxonly", mbuf_size="enable")

    def test_perf_enable_header_split(self):
        self.perf_test(
            fwd_mode="rxonly", mbuf_size="enable", header_split="udp", pkt_type="ip"
        )
        self.perf_test(
            fwd_mode="rxonly", mbuf_size="enable", header_split="udp", pkt_type="udp"
        )

    def test_perf_disable_header_split(self):
        self.perf_test(fwd_mode="io")
        self.perf_test(fwd_mode="io", mbuf_size="enable")

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
