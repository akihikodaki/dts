# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2021 Intel Corporation
#

"""
DPDK Test suite ICE_dcf_qos
Intel® Ethernet 800 Series configure QoS for vf/vsi in DCF
Support ETS-based QoS configuration, including Arbiters configuration (strict priority, WFQ)
and BW Allocation and limitation.
"""
import operator
import os
import re
import time
import traceback
from copy import deepcopy
from pprint import pformat

from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.pktgen import TRANSMIT_CONT
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE, NICS, get_nic_name
from framework.test_case import TestCase


class TestICEDcfQos(TestCase):
    def d_con(self, cmd):
        _cmd = [cmd, "# ", 15] if isinstance(cmd, str) else cmd
        return self.dut.send_expect(*_cmd)

    def d_a_con(self, cmds):
        prompt = "# "
        if isinstance(cmds, str):
            _cmd = [cmds, prompt, 20]
            return self.dut.alt_session.send_expect(*_cmd)
        else:
            return [self.dut.alt_session.send_expect(_cmd, prompt, 20) for _cmd in cmds]

    def pmd_con(self, cmds):
        prompt = "testpmd> "
        if isinstance(cmds, str):
            _cmd = [cmds, prompt, 20]
            return self.d_con(_cmd)
        else:
            outputs = []
            for _cmd in cmds:
                if isinstance(_cmd, list):
                    _cmd, func = _cmd
                    output = self.d_con([_cmd, prompt, 10])
                    if func and callable(func):
                        func(output)
                else:
                    output = self.d_con([_cmd, prompt, 10])
                outputs.append(output)
            return outputs

    def get_pkt_len(self, frame_size):
        HEADER_SIZE["vlan"] = 4
        headers_size = sum([HEADER_SIZE[x] for x in ["eth", "ip", "vlan", "udp"]])
        pktlen = frame_size - headers_size
        return pktlen

    def config_stream(self, fields, frame_size):
        vlan_id, pri, mac = fields + [None] * (3 - len(fields))
        dmac = mac or "00:11:22:33:44:55"
        pkt_name = "VLAN_UDP"
        pkt_config = {
            "type": pkt_name.upper(),
            "pkt_layers": {
                "ether": {"dst": dmac},
                "vlan": {"vlan": vlan_id, "prio": pri},
                "raw": {"payload": ["58"] * self.get_pkt_len(frame_size)},
            },
        }
        values = pkt_config
        pkt_type = values.get("type")
        pkt_layers = values.get("pkt_layers")
        pkt = Packet(pkt_type=pkt_type)
        for layer in list(pkt_layers.keys()):
            pkt.config_layer(layer, pkt_layers[layer])
        return pkt.pktgen.pkt

    def add_stream_to_pktgen(self, txport, rxport, send_pkts, option):
        stream_ids = []
        for pkt in send_pkts:
            _option = deepcopy(option)
            _option["pcap"] = pkt
            stream_id = self.tester.pktgen.add_stream(txport, rxport, send_pkts[0])
            self.tester.pktgen.config_stream(stream_id, _option)
            stream_ids.append(stream_id)
        return stream_ids

    def traffic(self, option):
        txport = option.get("tx_intf")
        rxport = option.get("rx_intf")
        rate_percent = option.get("rate_percent", float(100))
        duration = option.get("duration", 20)
        send_pkts = option.get("stream") or []
        self.tester.pktgen.clear_streams()
        s_option = {
            "stream_config": {
                "txmode": {},
                "transmit_mode": TRANSMIT_CONT,
                "rate": rate_percent,
            },
            "fields_config": {
                "ip": {
                    "src": {
                        "start": "198.18.0.0",
                        "end": "198.18.0.255",
                        "step": 1,
                        "action": "random",
                    },
                },
            },
        }
        stream_ids = self.add_stream_to_pktgen(txport, rxport, send_pkts, s_option)
        traffic_opt = {
            "method": "throughput",
            "duration": duration,
            "interval": duration - 5,
            "callback": self.testpmd_query_stats,
        }
        result = self.tester.pktgen.measure(stream_ids, traffic_opt)
        return result

    def check_traffic(self, stream_configs, traffic_tasks, frame_size=68):
        tester_rx_port_id = tester_tx_port_id = self.tester.get_local_port(
            self.dut_ports[0]
        )
        duration = 20
        results = []
        _traffic_tasks = traffic_tasks[:]
        for index, traffic_task in enumerate(_traffic_tasks):
            stream_ids, rate_percent, _ = traffic_task
            streams = []
            for idx in stream_ids:
                streams.append(self.config_stream(stream_configs[idx], frame_size))
            ports_topo = {
                "tx_intf": tester_tx_port_id,
                "rx_intf": tester_rx_port_id,
                "stream": streams,
                "duration": duration,
                "rate_percent": rate_percent,
            }
            result = self.traffic(ports_topo)
            queue_stats = self.get_queue_packets_stats()
            results.append([result, self.pmd_stat, queue_stats])
            time.sleep(5)

        for traffic_task, _result in zip(_traffic_tasks, results):
            stream_ids, _, expected_t = traffic_task
            result, pmd_stat, queue_stats = _result

            if not isinstance(expected_t, list):
                expected_t = [expected_t]
            for _expected_t in expected_t:
                _expected_t = list(_expected_t) + [None] * (3 - len(_expected_t))
                status = self.is_expected_throughput(_expected_t, pmd_stat)
                msg = (
                    f"{pformat(traffic_task)}"
                    " not get expected throughput value, real is: "
                    f"{pformat(pmd_stat)}"
                )
                self.verify(status, msg)
        return results

    def is_expected_throughput(self, expected, pmd_stat):
        _expected, unit, port = expected
        port = port or 1
        real_stat = pmd_stat.get(f"port {port}", {})
        if unit == "rGbps":
            key = "rx_bps"
        else:
            key = "tx_bps"
        real_bps = real_stat.get(key) or 0
        if real_bps == 0 and _expected == 0:
            return True
        if not _expected:
            return False
        bias = 10
        if unit == "MBps":
            return (100 * (real_bps / 8 / 1e6 - _expected) / _expected) < abs(bias)
        elif unit == "-MBps":
            return real_bps / 8 / 1e6 < _expected
        elif unit in ["Gbps", "rGbps"]:
            return (100 * (real_bps / 1e9 - _expected) / _expected) < abs(bias)
        return True

    def get_custom_nic_port(self, nic_name, num=None):
        cnt = 0
        for dut_port_id in self.dut.get_ports():
            port_type = self.dut.ports_info[dut_port_id]["type"]
            intf = self.dut.ports_info[dut_port_id]["intf"]
            pci = self.dut.ports_info[dut_port_id]["pci"]
            _nic_name = get_nic_name(port_type)
            if _nic_name in nic_name:
                if num and cnt != num:
                    cnt += 1
                    continue
                return dut_port_id, intf, pci
        return None, None, None

    def pf_preset(self, num=None):
        self.nic_100g, self.nic100G_intf, self.nic100g_pci = self.get_custom_nic_port(
            [
                "ICE_100G-E810C_QSFP",
            ],
            num=num,
        )
        self.nic_25g, self.nic25G_intf, self.nic25g_pci = self.get_custom_nic_port(
            [
                "ICE_25G-E810_XXV_SFP",
            ]
        )
        msg = "not enough nics for testing"
        self.verify(self.nic_100g is not None and self.nic_25g is not None, msg)
        port_obj = self.dut.ports_info[self.nic_100g]["port"]
        port_obj.bind_driver(port_obj.default_driver)
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf} --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
            f"lldptool -T -i {self.nic25G_intf} -V ETS-CFG willing=no",
            f"lldptool -T -i {self.nic100G_intf} -V ETS-CFG willing=no",
        ]
        self.d_a_con(cmds)
        port_obj = self.dut.ports_info[self.nic_25g]["port"]
        port_obj.bind_driver(port_obj.default_driver)

    def pf_restore(self):
        port_obj = self.dut.ports_info[self.nic_100g]["port"]
        port_obj.bind_driver(self.drivername)
        port_obj = self.dut.ports_info[self.nic_25g]["port"]
        port_obj.bind_driver(self.drivername)

    def vf_init(self):
        self.cur_vf_config = {}
        self.vf_ports_info = {}
        self.valports = []

    def vf_create(self, valports, vf_num=2):
        vf_config = {
            "valports": valports or [self.nic_100g],
            "vf_num": vf_num,
        }
        if operator.eq(vf_config, self.cur_vf_config) and self.vf_ports_info:
            return
        elif self.vf_ports_info:
            self.vf_destroy()
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf} --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
            f"rmmod {self.drivername}",
            f"modprobe {self.drivername}",
        ]
        self.d_a_con(cmds)
        for index, port_id in enumerate(valports):
            port_obj = self.dut.ports_info[port_id]["port"]
            pf_driver = port_obj.default_driver
            self.dut.generate_sriov_vfs_by_port(port_id, vf_num, driver=pf_driver)
            pf_pci = port_obj.pci
            sriov_vfs_port = self.dut.ports_info[port_id].get("vfs_port")
            if not sriov_vfs_port:
                msg = f"failed to create vf on dut port {pf_pci}"
                self.logger.error(msg)
                continue
            for port in sriov_vfs_port:
                port.bind_driver(driver=self.drivername)
            self.vf_ports_info[port_id] = {
                "pf_pci": pf_pci,
                "vfs_pci": port_obj.get_sriov_vfs_pci(),
            }
            time.sleep(1)
            pf_intf = port_obj.get_interface_name()
            cmd = ";".join(
                [
                    f"ifconfig {pf_intf} up",
                    f"ethtool {pf_intf} | grep Speed",
                ]
            )
            self.d_a_con(cmd)
            set_mac = "00:11:22:33:44:55" if index == 0 else "00:11:22:33:44:66"
            set_mac_cmd = f"ip link set {pf_intf} vf 1 mac {set_mac}"
            cmds = [
                set_mac_cmd if vf_num == 2 else "echo 'set mac in next step'",
                f"ip link set dev {pf_intf} vf 0 trust on",
            ]
            self.d_a_con(cmds)
        self.cur_vf_config = vf_config

    def vf_destroy(self):
        if not self.vf_ports_info:
            return
        for port_id, _ in self.vf_ports_info.items():
            port_obj = self.dut.ports_info[port_id]["port"]
            pf_intf = port_obj.get_interface_name()
            cmd = f"ip link set dev {pf_intf} vf 0 trust off"
            self.d_a_con(cmd)
            self.dut.destroy_sriov_vfs_by_port(port_id)
            pf_driver = port_obj.default_driver
            port_obj.bind_driver(pf_driver)
        self.vf_ports_info = {}
        self.cur_vf_config = {}
        cmds = [
            "rmmod ice",
            "modprobe ice",
        ]
        self.d_a_con(cmds)

    def testpmd_query_stats(self):
        output = self.pmd_con("show port stats all")
        if not output:
            return
        port_pat = ".*NIC statistics for (port \d+) .*"
        rx_pat = ".*Rx-pps:\s+(\d+)\s+Rx-bps:\s+(\d+).*"
        tx_pat = ".*Tx-pps:\s+(\d+)\s+Tx-bps:\s+(\d+).*"
        port = re.findall(port_pat, output, re.M)
        rx = re.findall(rx_pat, output, re.M)
        tx = re.findall(tx_pat, output, re.M)
        if not port or not rx or not tx:
            return
        stat = {}
        for port_id, (rx_pps, rx_bps), (tx_pps, tx_bps) in zip(port, rx, tx):
            stat[port_id] = {
                "rx_pps": float(rx_pps),
                "rx_bps": float(rx_bps),
                "tx_pps": float(tx_pps),
                "tx_bps": float(tx_bps),
            }
        self.pmd_stat = stat

    def get_queue_packets_stats(self):
        output = self.pmd_con("stop")
        self.pmd_con("start")
        pat_k = r"Forward Stats for RX Port= ([0-9]+)/Queue= ([0-9]+)\s+-> TX Port= ([0-9]+)/Queue= ([0-9]+)"
        pat_v = r"RX-packets: ([0-9]+)\s+TX-packets: ([0-9]+)\s+TX-dropped: ([0-9]+)"
        k_result = re.findall(pat_k, output, re.M)
        v_result = re.findall(pat_v, output, re.M)
        if not k_result or not v_result:
            return {}
        stats = dict(zip(k_result, v_result))
        return stats

    def check_queue(self, expecteds, reals):
        if not expecteds:
            return
        if not isinstance(expecteds, list):
            expecteds = [expecteds]
        queue_map_grp = []
        for expected in expecteds:
            queue_map_grp += [
                tuple(
                    [
                        str(item)
                        for item in [expected[0][0], queue_id, expected[0][1], queue_id]
                    ]
                )
                for queue_id in expected[1]
            ]
        for real, _ in reals.items():
            if real not in queue_map_grp:
                msg = " not get expected queue mapping, real is: " f"{pformat(reals)}"
                self.verify(False, msg)

    def check_queue_pkts_ratio(self, expected, result):
        total_pkts = 0
        for key, value in result.items():
            total_pkts += int(value[1])
        ratio = []
        for queue in expected:
            if isinstance(queue[0], list):
                e_keys = []
                for _queue in queue[0]:
                    topo = [str(i) for i in _queue[0]]
                    queue_ids = [str(i) for i in _queue[1]]
                    e_keys += [
                        (
                            topo[0],
                            queue_id,
                            topo[1],
                            queue_id,
                        )
                        for queue_id in queue_ids
                    ]
            else:
                topo = [str(i) for i in queue[0]]
                queue_ids = [str(i) for i in queue[1]]
                e_keys = [
                    (
                        topo[0],
                        queue_id,
                        topo[1],
                        queue_id,
                    )
                    for queue_id in queue_ids
                ]
            e_total = 0
            for key, value in result.items():
                if key in e_keys:
                    e_total += int(value[1])
            if not e_total:
                ratio.append(0)
                continue
            percentage = 100 * e_total / total_pkts
            ratio.append(percentage)
        bias = 10
        for idx, queue in enumerate(expected):
            percentage = 100 * queue[2] / sum([i[2] for i in expected])

            _bias = 100 * abs(ratio[idx] - percentage) / percentage
            self.logger.info((ratio[idx], percentage))
            if _bias < bias:
                continue
            else:
                msg = "can not get expected queue ratio"
                self.verify(False, msg)

    def testpmd_init(self):
        self.pmd_output = PmdOutput(self.dut)
        self.is_pmd_on = False

    def testpmd_start(self, vfs_group):
        allow_list = []
        for vfs in vfs_group:
            for idx, vf in enumerate(vfs):
                addr = f"{vf},cap=dcf" if idx == 0 else vf
                allow_list.append(addr)
        eal_param = " ".join(allow_list)
        param = ("{xq} " "{nb-cores} " "{topo}").format(
            **{
                "xq": "--txq=8 --rxq=8",
                "nb-cores": "--nb-cores=8",
                "topo": "--port-topology=loop" if len(vfs_group) == 1 else "",
            }
        )
        self.pmd_output.start_testpmd(
            cores="1S/9C/1T", param=param, **{"ports": allow_list}
        )
        self.is_pmd_on = True

    def testpmd_close(self):
        if not self.is_pmd_on:
            return
        try:
            self.pmd_con("stop")
            self.d_con(["quit", "# ", 30])
        except Exception as e:
            self.logger.error(traceback.format_exc())
        self.is_pmd_on = False

    def check_output(self, expected, output):
        if isinstance(expected, str):
            expected = [expected]
        for _expected in expected:
            self.verify(
                _expected in output, f"expected <{_expected}> message not display"
            )

    def check_error_output(self, output):
        msg = "'port tm hierarchy commit' failed to set"
        self.verify("error" not in output.lower(), msg)
        self.verify("fail" not in output.lower(), msg)

    def strict_mode_check_peak_tb_rate_preset(
        self, vfs_grp, dcb_cmd=None, if_op="up", commit_check=True
    ):
        cmds = [
            dcb_cmd
            or f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} {if_op}",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmds = [
            "port stop all",
            "add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0",
            [
                "port tm hierarchy commit 0 no",
                self.check_error_output if commit_check else None,
            ],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 700 0 1 2 0 0 0xffffffff 0 0",
            [
                "port tm hierarchy commit 1 no",
                self.check_error_output if commit_check else None,
            ],
            "port start all",
            "set fwd mac",
            "start",
        ]
        self.pmd_con(cmds)

    def verify_strict_mode_check_peak_tb_rate(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmds = [
            "port stop all",
            "add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 no", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 700 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 1 no", self.check_error_output],
            "port start all",
            "set fwd mac",
            "start",
        ]
        self.pmd_con(cmds)
        stream_configs = [
            [0, 2],
            [0, 5],
            [0, 3],
            [0, 4],
        ]
        traffic_tasks = [
            [[0], 25, (2, "MBps")],
            [[1], 25, (2, "MBps")],
            [[2], 25, (4, "MBps")],
            [[3], 25, (4, "MBps")],
            [[0, 1, 2, 3], 100, (10, "MBps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks)
        self.testpmd_close()
        queue_mapping = [
            ((1, 1), range(4)),
            ((1, 1), range(4)),
            ((1, 1), (4, 5)),
            ((1, 1), (6, 7)),
            None,
        ]
        [
            self.check_queue(expected, real[2])
            for expected, real in zip(queue_mapping, results)
        ]
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmds = [
            "port stop all",
            "add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 no", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 800 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 1 no", self.check_error_output],
            "port start all",
            "set fwd mac",
            "start",
        ]
        self.pmd_con(cmds)
        traffic_tasks = [
            [[0], 25, (2, "MBps")],
            [[1], 25, (2, "MBps")],
            [[2], 25, (4, "MBps")],
            [[3], 25, (0, "MBps")],
            [[0, 1, 2, 3], 100, (6, "MBps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks)
        self.testpmd_close()

    def verify_ets_mode_check_peak_tb_rate(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf} --ieee --up2tc 0,0,0,0,1,1,1,1 --tcbw 20,80,0,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0",
            f"{self.dcbgetset} {self.nic25G_intf} --ieee --up2tc 0,0,0,0,1,1,1,1 --tcbw 20,80,0,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
            f"ifconfig {self.nic25G_intf} up",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)

        def pmd_cmds(pir=None):
            return [
                "set portlist 0,2,1,3",
                "show config fwd",
                "port stop all",
                f"add port tm node shaper profile 0 1 10000000 0 {pir or 4000000000} 0 0 0",
                "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
                "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
                "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
                "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
                "add port tm leaf node 0 2 800 0 1 2 1 0 0xffffffff 0 0",
                "add port tm leaf node 0 3 800 0 1 2 1 0 0xffffffff 0 0",
                ["port tm hierarchy commit 0 yes", self.check_error_output],
                f"add port tm node shaper profile 2 1 10000000 0 {pir or 1000000000} 0 0 0",
                "add port tm nonleaf node 2 1000 -1 0 1 0 -1 1 0 0",
                "add port tm nonleaf node 2 900 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 2 800 1000 0 1 1 -1 1 0 0",
                "add port tm leaf node 2 0 900 0 1 2 1 0 0xffffffff 0 0",
                "add port tm leaf node 2 1 900 0 1 2 1 0 0xffffffff 0 0",
                "add port tm leaf node 2 2 800 0 1 2 1 0 0xffffffff 0 0",
                "add port tm leaf node 2 3 800 0 1 2 1 0 0xffffffff 0 0",
                ["port tm hierarchy commit 2 yes", self.check_error_output],
                "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
                "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
                "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 1 7 800 0 1 2 0 0 0xffffffff 0 0",
                ["port tm hierarchy commit 1 yes", self.check_error_output],
                "add port tm nonleaf node 3 1000 -1 0 1 0 0 1 0 0",
                "add port tm nonleaf node 3 900 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 3 800 1000 0 1 1 0 1 0 0",
                "add port tm leaf node 3 0 900 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 3 1 900 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 3 2 900 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 3 3 900 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 3 4 800 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 3 5 800 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 3 6 800 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 3 7 800 0 1 2 0 0 0xffffffff 0 0",
                ["port tm hierarchy commit 3 yes", self.check_error_output],
                "port start all",
                "set fwd mac",
                "start",
            ]

        self.pmd_con(pmd_cmds())
        stream_configs = [
            [0, 0],
            [0, 4],
        ]
        traffic_tasks = [
            [[0], 50, (7.3, "Gbps", 3)],
            [[1], 50, (7.3, "Gbps", 3)],
            [[0, 1], 100, (7.3, "Gbps", 3)],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks)
        self.pmd_con("stop")
        self.testpmd_close()

        queue_mapping = [
            ((1, 3), range(4)),
            ((1, 3), range(4, 8)),
            None,
        ]
        [
            self.check_queue(expected, real[2])
            for expected, real in zip(queue_mapping, results)
        ]
        expected = [
            ((1, 3), range(4), 20),
            ((1, 3), range(4, 8), 80),
        ]
        self.check_queue_pkts_ratio(expected, results[-1][2])
        time.sleep(5)
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf} --ieee --up2tc 0,0,0,0,1,1,1,1 --tcbw 20,80,0,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0",
            f"{self.dcbgetset} {self.nic25G_intf} --ieee --up2tc 0,0,0,0,1,1,1,1 --tcbw 20,80,0,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
            f"ifconfig {self.nic25G_intf} up",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        self.pmd_con(pmd_cmds(500000000))
        traffic_tasks = [
            [[0], 50, (3.95, "Gbps", 3)],
            [[1], 50, (3.95, "Gbps", 3)],
            [[0, 1], 100, (7.27, "Gbps", 3)],
        ]
        result = self.check_traffic(stream_configs, traffic_tasks)
        self.pmd_con("stop")
        self.testpmd_close()

    def verify_strict_mode_check_cmit_tb_rate(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf} --ieee --up2tc 0,0,0,1,0,0,0,0 --tcbw 10,90,0,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"{self.dcbgetset} {self.nic25G_intf} --ieee --up2tc 0,0,0,1,0,0,0,0 --tcbw 10,90,0,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
            f"ifconfig {self.nic25G_intf} up",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmds = [
            "set portlist 0,2,1,3",
            "show config fwd",
            "port stop all",
            "add port tm node shaper profile 0 1 10000000 0 4000000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 1 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 yes", self.check_error_output],
            "add port tm node shaper profile 2 1 10000000 0 1000000000 0 0 0",
            "add port tm nonleaf node 2 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 2 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 2 800 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 2 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 2 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 2 2 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 2 3 800 0 1 2 1 0 0xffffffff 0 0",
            ["port tm hierarchy commit 2 yes", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 800 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 1 yes", self.check_error_output],
            "add port tm nonleaf node 3 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 3 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 3 800 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 3 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 6 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 7 800 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 3 yes", self.check_error_output],
            "port start all",
            "set fwd mac",
            "start",
        ]
        self.pmd_con(cmds)
        stream_configs = [
            [0, 0],
            [0, 3],
        ]
        traffic_tasks = [
            [[0], 50, (7.3, "Gbps", 3)],
            [[1], 50, (7.3, "Gbps", 3)],
            [[0, 1], 100, (7.3, "Gbps", 3)],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks)
        self.pmd_con("stop")
        self.testpmd_close()

        queue_mapping = [
            ((1, 3), range(4)),
            ((1, 3), range(4, 8)),
            None,
        ]
        [
            self.check_queue(expected, real[2])
            for expected, real in zip(queue_mapping, results)
        ]

    def verify_ets_mode_check_TC_throughput_min_BW_allocation(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,0,1,1,2,2,2,2 --tcbw 1,10,89,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0",
            f"{self.dcbgetset} {self.nic25G_intf}  --ieee --up2tc 0,0,1,1,2,2,2,2 --tcbw 1,10,89,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
            f"ifconfig {self.nic25G_intf} up",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmds = [
            "set portlist 0,2,1,3",
            "show config fwd",
            "port stop all",
            "add port tm node shaper profile 0 1 1000000000 0 4000000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 700 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 700 0 1 2 1 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 yes", self.check_error_output],
            "add port tm node shaper profile 2 1 100000000 0 1000000000 0 0 0",
            "add port tm node shaper profile 2 2 100000000 0 150000000 0 0 0",
            "add port tm nonleaf node 2 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 2 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 2 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 2 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 2 0 900 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 2 1 900 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 2 2 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 2 3 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 2 4 700 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 2 5 700 0 1 2 1 0 0xffffffff 0 0",
            ["port tm hierarchy commit 2 yes", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 700 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 1 yes", self.check_error_output],
            "add port tm nonleaf node 3 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 3 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 3 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 3 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 3 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 2 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 3 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 6 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 7 700 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 3 yes", self.check_error_output],
            "port start all",
            "set fwd mac",
            "start",
        ]
        self.pmd_con(cmds)
        stream_configs = [
            [0, 0],
            [0, 1],
            [0, 2],
            [0, 3],
            [0, 4],
            [0, 5],
            [0, 6],
            [0, 7],
        ]
        traffic_tasks = [
            [[0], 12.5, (1.2, "Gbps", 3)],
            [[1], 12.5, (1.2, "Gbps", 3)],
            [[2], 12.5, (1.2, "Gbps", 3)],
            [[3], 12.5, (1.2, "Gbps", 3)],
            [[4], 12.5, (8, "Gbps", 3)],
            [[5], 12.5, (8, "Gbps", 3)],
            [[6], 12.5, (8, "Gbps", 3)],
            [[7], 12.5, (8, "Gbps", 3)],
            [[0, 1, 2, 3, 4, 5, 6, 7], 100, (9.7, "Gbps", 1)],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks, frame_size=1024)
        queue_mapping = [
            ((1, 3), range(2)),
            ((1, 3), range(2)),
            ((1, 3), range(2, 6)),
            ((1, 3), range(2, 6)),
            ((1, 3), (6, 7)),
            ((1, 3), (6, 7)),
            ((1, 3), (6, 7)),
            ((1, 3), (6, 7)),
            None,
        ]
        [
            self.check_queue(expected, real[2])
            for expected, real in zip(queue_mapping, results)
        ]
        time.sleep(10)
        traffic_tasks = [
            [[0, 1, 2, 3, 4, 5, 6, 7], 100, (7.273, "Gbps", 1)],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks, frame_size=68)
        self.testpmd_close()
        expected = [
            ((1, 3), range(2), 1),
            ((1, 3), range(2, 6), 9),
            ((1, 3), range(6, 8), 89),
        ]
        self.check_queue_pkts_ratio(expected, results[-1][2])

    def verify_iavf_VFs_strict_mode_check_peak_tb_rate(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
            f"ip link set dev {self.nic100G_intf} vf 0 trust on",
            f"ip link set {self.nic100G_intf} vf 1 mac 00:11:22:33:44:55",
            f"ip link set {self.nic100G_intf} vf 2 mac 00:11:22:33:44:66",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmds = [
            "port stop all",
            "add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 -1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 -1 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 6 700 0 1 2 -1 0 0xffffffff 0 0",
            "add port tm leaf node 0 7 700 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 8 700 0 1 2 2 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 yes", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 700 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 1 yes", self.check_error_output],
            "add port tm nonleaf node 2 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 2 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 2 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 2 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 2 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 2 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 3 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 6 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 7 700 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 2 yes", self.check_error_output],
            "port start all",
            "set fwd mac",
            "start",
        ]
        self.pmd_con(cmds)
        stream_configs = [
            [0, 1, "00:11:22:33:44:55"],
            [0, 2, "00:11:22:33:44:55"],
            [0, 3, "00:11:22:33:44:55"],
            [0, 4, "00:11:22:33:44:55"],
            [0, 1, "00:11:22:33:44:66"],
            [0, 2, "00:11:22:33:44:66"],
            [0, 3, "00:11:22:33:44:66"],
            [0, 4, "00:11:22:33:44:66"],
        ]
        traffic_tasks = [
            [[0], 12.5, (2, "MBps")],
            [[1], 12.5, (2, "MBps")],
            [[2], 12.5, (4, "MBps")],
            [[3], 12.5, (2, "MBps")],
            [[4], 12.5, (2, "MBps", 2)],
            [[5], 12.5, (2, "MBps", 2)],
            [[6], 12.5, (2, "MBps", 2)],
            [[7], 12.5, (4, "MBps", 2)],
            [[0, 1, 2, 3, 4, 5, 6, 7], 100, (12.5, "Gbps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks)
        self.testpmd_close()

        expected = [
            ((1, 1), range(2)),
            ((1, 1), range(2)),
            ((1, 1), range(2, 4)),
            ((1, 1), range(4, 8)),
            ((1, 2), range(2)),
            ((1, 2), range(2)),
            ((1, 2), range(2, 6)),
            ((1, 2), range(6, 8)),
            None,
        ]
        expected = [
            ((1, 1), range(2), 16),
            ((1, 1), range(2, 4), 32),
            ((1, 1), range(4, 8), 16),
            ((2, 2), range(2), 16),
            ((2, 2), range(2, 6), 16),
            ((2, 2), range(6, 8), 32),
        ]
        self.check_queue_pkts_ratio(expected, results[-1][2])

    def verify_iavf_VFs_strict_mode_check_cmit_tb_rate(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf} --ieee --up2tc 0,0,0,1,0,0,0,0 --tcbw 20,80,0,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"{self.dcbgetset} {self.nic25G_intf} --ieee --up2tc 0,0,0,1,0,0,0,0 --tcbw 20,80,0,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            "sleep 5",
            f"ifconfig {self.nic100G_intf} up",
            f"ifconfig {self.nic25G_intf} up",
            "sleep 5",
            f"ip link set dev {self.nic100G_intf} vf 0 trust on",
            "sleep 5",
            f"ip link set {self.nic100G_intf} vf 1 mac 00:11:22:33:44:55",
            f"ip link set {self.nic100G_intf} vf 2 mac 00:11:22:33:44:66",
            "sleep 5",
            f"ip link set dev {self.nic25G_intf} vf 0 trust on",
            "sleep 5",
            f"ip link set {self.nic25G_intf} vf 1 mac 00:11:22:33:44:77",
            f"ip link set {self.nic25G_intf} vf 2 mac 00:11:22:33:44:88",
            "sleep 5",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmds = [
            "set portlist 0,3,1,4,2,5",
            "show config fwd",
            "port stop all",
            "add port tm node shaper profile 0 1 100000000 0 4000000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 800 0 1 2 1 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 no", self.check_error_output],
            "add port tm node shaper profile 3 1 100000000 0 500000000 0 0 0",
            "add port tm nonleaf node 3 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 3 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 3 800 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 3 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 3 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 3 2 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 3 3 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 3 4 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 3 5 800 0 1 2 1 0 0xffffffff 0 0",
            ["port tm hierarchy commit 3 no", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 800 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 1 no", self.check_error_output],
            "add port tm nonleaf node 4 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 4 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 4 800 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 4 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 4 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 4 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 4 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 4 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 4 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 4 6 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 4 7 800 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 4 no", self.check_error_output],
            "add port tm nonleaf node 2 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 2 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 2 800 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 2 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 2 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 3 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 6 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 7 800 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 2 no", self.check_error_output],
            "add port tm nonleaf node 5 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 5 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 5 800 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 5 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 5 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 5 2 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 5 3 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 5 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 5 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 5 6 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 5 7 800 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 5 no", self.check_error_output],
        ]
        self.pmd_con(cmds)
        time.sleep(15)
        cmds = [
            "port start all",
            "set fwd mac",
            "start",
        ]
        self.pmd_con(cmds)
        time.sleep(15)
        stream_configs = [
            [0, 2, "00:11:22:33:44:55"],
            [0, 3, "00:11:22:33:44:55"],
            [0, 2, "00:11:22:33:44:66"],
            [0, 3, "00:11:22:33:44:66"],
        ]
        traffic_tasks = [
            [
                [
                    0,
                    1,
                    2,
                    3,
                ],
                100,
                [(3.64, "Gbps", 4), (3.64, "Gbps", 5)],
            ],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks)
        self.pmd_con("stop")
        self.testpmd_close()

    def verify_iavf_VFs_ets_mode(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0",
            f"{self.dcbgetset} {self.nic25G_intf}  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
            f"ifconfig {self.nic25G_intf} up",
        ]
        self.d_a_con(cmds)
        cmds = [
            f"ip link set dev {self.nic100G_intf} vf 0 trust on",
            f"ip link set {self.nic100G_intf} vf 1 mac 00:11:22:33:44:55",
            f"ip link set {self.nic100G_intf} vf 2 mac 00:11:22:33:44:66",
            f"ip link set dev {self.nic25G_intf} vf 0 trust on",
            f"ip link set {self.nic25G_intf} vf 1 mac 00:11:22:33:44:77",
            f"ip link set {self.nic25G_intf} vf 2 mac 00:11:22:33:44:88",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmds = [
            "set portlist 0,3,1,4,2,5",
            "show config fwd",
            "port stop all",
            "add port tm node shaper profile 0 1 0 0 0 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 6 700 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 7 700 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 8 700 0 1 2 1 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 yes", self.check_error_output],
            "add port tm node shaper profile 3 1 0 0 0 0 0 0",
            "add port tm nonleaf node 3 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 3 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 3 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 3 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 3 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 3 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 3 2 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 3 3 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 3 4 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 3 5 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 3 6 700 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 3 7 700 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 3 8 700 0 1 2 1 0 0xffffffff 0 0",
            ["port tm hierarchy commit 3 yes", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 700 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 1 yes", self.check_error_output],
            "add port tm nonleaf node 2 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 2 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 2 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 2 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 2 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 2 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 3 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 6 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 2 7 700 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 2 yes", self.check_error_output],
            "add port tm nonleaf node 4 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 4 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 4 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 4 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 4 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 4 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 4 2 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 4 3 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 4 4 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 4 5 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 4 6 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 4 7 700 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 4 yes", self.check_error_output],
            "add port tm nonleaf node 5 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 5 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 5 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 5 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 5 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 5 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 5 2 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 5 3 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 5 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 5 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 5 6 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 5 7 700 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 5 yes", self.check_error_output],
            "port start all",
            "set fwd mac",
            "start",
        ]
        self.pmd_con(cmds)
        time.sleep(25)
        stream_configs = [
            [0, 1, "00:11:22:33:44:55"],
            [0, 2, "00:11:22:33:44:55"],
            [0, 3, "00:11:22:33:44:55"],
            [0, 4, "00:11:22:33:44:55"],
            [0, 1, "00:11:22:33:44:66"],
            [0, 2, "00:11:22:33:44:66"],
            [0, 3, "00:11:22:33:44:66"],
            [0, 4, "00:11:22:33:44:66"],
        ]
        traffic_tasks = [
            [[0], 12.5, (7.27, "Gbps", 4)],
            [[1], 12.5, (7.27, "Gbps", 4)],
            [[2], 12.5, (7.27, "Gbps", 4)],
            [[3], 12.5, (7.27, "Gbps", 4)],
            [[4], 12.5, (7.27, "Gbps", 5)],
            [[5], 12.5, (7.27, "Gbps", 5)],
            [[6], 12.5, (7.27, "Gbps", 5)],
            [[7], 12.5, (7.27, "Gbps", 5)],
            [[0, 1, 2, 3, 4, 5, 6, 7], 100, [(3.63, "Gbps", 4), (3.63, "Gbps", 5)]],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks)
        self.testpmd_close()
        expected = [
            ([[(1, 4), range(2)], [(2, 5), range(2)]], None, 1),
            ([[(1, 4), range(2, 4)], [(2, 5), range(2, 6)]], None, 3),
            ([[(1, 4), range(4, 8)], [(2, 5), range(6, 8)]], None, 6),
        ]
        self.check_queue_pkts_ratio(expected, results[-1][2])

    def verify_strict_mode_8_TCs(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,1,2,3,4,5,6,7 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmds = [
            "port stop all",
            "add port tm node shaper profile 0 1 1000000 0 400000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 200000000 0 0 0",
            "add port tm node shaper profile 0 3 1000000 0 100000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 600 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 500 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 400 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 300 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 200 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 3 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 3 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 3 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 3 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 700 0 1 2 3 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 700 0 1 2 3 0 0xffffffff 0 0",
            "add port tm leaf node 0 6 600 0 1 2 3 0 0xffffffff 0 0",
            "add port tm leaf node 0 7 600 0 1 2 3 0 0xffffffff 0 0",
            "add port tm leaf node 0 8 500 0 1 2 3 0 0xffffffff 0 0",
            "add port tm leaf node 0 9 500 0 1 2 3 0 0xffffffff 0 0",
            "add port tm leaf node 0 10 400 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 11 400 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 12 300 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 13 300 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 14 200 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 15 200 0 1 2 1 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 yes", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 600 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 500 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 400 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 300 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 200 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 600 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 500 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 400 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 300 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 200 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 1 yes", self.check_error_output],
            "port start all",
            "set fwd mac",
            "start",
        ]
        self.pmd_con(cmds)
        stream_configs = [
            [0, 0],
            [0, 1],
            [0, 2],
            [0, 3],
            [0, 4],
            [0, 5],
            [0, 6],
            [0, 7],
        ]
        traffic_tasks = [
            [[0, 1, 2, 3, 4, 5, 6, 7], 100, (10, "Gbps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks, frame_size=68)
        self.testpmd_close()
        time.sleep(10)
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,1,2,3,4,5,6,7 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmds = [
            "port stop all",
            "add port tm node shaper profile 0 1 1000000 0 1780000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 600 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 500 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 400 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 300 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 200 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 700 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 700 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 6 600 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 7 600 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 8 500 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 9 500 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 10 400 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 11 400 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 12 300 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 13 300 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 14 200 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 15 200 0 1 2 1 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 yes", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 600 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 500 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 400 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 300 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 200 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 600 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 500 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 400 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 300 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 200 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 1 yes", self.check_error_output],
            "port start all",
            "set fwd mac",
            "start",
        ]
        self.pmd_con(cmds)
        traffic_tasks = [
            [[0, 1, 2, 3, 4, 5, 6, 7], 100, (25, "Gbps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks, frame_size=68)
        self.pmd_con("stop")
        time.sleep(5)
        self.pmd_con("start")
        time.sleep(10)
        traffic_tasks = [
            [[0, 1, 2, 3, 4, 5, 6, 7], 100, (100, "Gbps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks, frame_size=1024)
        self.testpmd_close()

    def verify_strict_mode_1_TC(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,0,0,0,0,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmds = [
            "port stop all",
            "add port tm node shaper profile 0 1 1000000 0 1000000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 yes", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 900 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 1 yes", self.check_error_output],
            "port start all",
            "set fwd mac",
            "start",
        ]
        self.pmd_con(cmds)
        stream_configs = [
            [0, 0],
            [0, 1],
            [0, 2],
            [0, 3],
            [0, 4],
            [0, 5],
            [0, 6],
            [0, 7],
        ]
        traffic_tasks = [
            [[0, 1, 2, 3, 4, 5, 6, 7], 100, (8, "Gbps")],
            [[0], 12.5, (8, "Gbps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks, frame_size=1024)
        self.testpmd_close()

    def verify_ets_mode_8_TCs(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,1,2,3,4,5,6,7 --tcbw 5,10,15,10,20,1,30,9 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0",
            f"{self.dcbgetset} {self.nic25G_intf}  --ieee --up2tc 0,1,2,3,4,5,6,7 --tcbw 5,10,15,10,20,1,30,9 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
            f"ifconfig {self.nic25G_intf} up",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)

        def pmd_cmds(opts):
            return [
                "set portlist 0,2,1,3",
                "show config fwd",
                "port stop all",
                "add port tm node shaper profile 0 1 1000000 0 4000000000 0 0 0",
                "add port tm node shaper profile 0 2 1000000 0 2000000000 0 0 0",
                "add port tm node shaper profile 0 3 1000000 0 1000000000 0 0 0",
                "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
                "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 0 600 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 0 500 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 0 400 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 0 300 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 0 200 1000 0 1 1 -1 1 0 0",
                "add port tm leaf node 0 0 900 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 0 1 900 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 0 2 800 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 0 3 800 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 0 4 700 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 0 5 700 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 0 6 600 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 0 7 600 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 0 8 500 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 0 9 500 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 0 10 400 0 1 2 2 0 0xffffffff 0 0",
                "add port tm leaf node 0 11 400 0 1 2 2 0 0xffffffff 0 0",
                "add port tm leaf node 0 12 300 0 1 2 2 0 0xffffffff 0 0",
                "add port tm leaf node 0 13 300 0 1 2 2 0 0xffffffff 0 0",
                "add port tm leaf node 0 14 200 0 1 2 1 0 0xffffffff 0 0",
                "add port tm leaf node 0 15 200 0 1 2 1 0 0xffffffff 0 0",
                ["port tm hierarchy commit 0 yes", self.check_error_output],
                opts[0],
                opts[1],
                opts[2],
                "add port tm nonleaf node 2 1000 -1 0 1 0 -1 1 0 0",
                "add port tm nonleaf node 2 900 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 2 800 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 2 700 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 2 600 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 2 500 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 2 400 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 2 300 1000 0 1 1 -1 1 0 0",
                "add port tm nonleaf node 2 200 1000 0 1 1 -1 1 0 0",
                "add port tm leaf node 2 0 900 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 2 1 900 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 2 2 800 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 2 3 800 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 2 4 700 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 2 5 700 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 2 6 600 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 2 7 600 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 2 8 500 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 2 9 500 0 1 2 3 0 0xffffffff 0 0",
                "add port tm leaf node 2 10 400 0 1 2 2 0 0xffffffff 0 0",
                "add port tm leaf node 2 11 400 0 1 2 2 0 0xffffffff 0 0",
                "add port tm leaf node 2 12 300 0 1 2 2 0 0xffffffff 0 0",
                "add port tm leaf node 2 13 300 0 1 2 2 0 0xffffffff 0 0",
                "add port tm leaf node 2 14 200 0 1 2 1 0 0xffffffff 0 0",
                "add port tm leaf node 2 15 200 0 1 2 1 0 0xffffffff 0 0",
                ["port tm hierarchy commit 2 yes", self.check_error_output],
                "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
                "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 1 600 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 1 500 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 1 400 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 1 300 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 1 200 1000 0 1 1 0 1 0 0",
                "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 1 1 800 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 1 2 700 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 1 3 600 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 1 4 500 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 1 5 400 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 1 6 300 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 1 7 200 0 1 2 0 0 0xffffffff 0 0",
                ["port tm hierarchy commit 1 yes", self.check_error_output],
                "add port tm nonleaf node 3 1000 -1 0 1 0 0 1 0 0",
                "add port tm nonleaf node 3 900 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 3 800 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 3 700 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 3 600 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 3 500 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 3 400 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 3 300 1000 0 1 1 0 1 0 0",
                "add port tm nonleaf node 3 200 1000 0 1 1 0 1 0 0",
                "add port tm leaf node 3 0 900 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 3 1 800 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 3 2 700 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 3 3 600 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 3 4 500 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 3 5 400 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 3 6 300 0 1 2 0 0 0xffffffff 0 0",
                "add port tm leaf node 3 7 200 0 1 2 0 0 0xffffffff 0 0",
                ["port tm hierarchy commit 3 yes", self.check_error_output],
                "port start all",
                "set fwd mac",
                "start",
            ]

        opts = [
            "add port tm node shaper profile 2 1 1000000 0 400000000 0 0 0",
            "add port tm node shaper profile 2 2 1000000 0 200000000 0 0 0",
            "add port tm node shaper profile 2 3 1000000 0 100000000 0 0 0",
        ]
        self.pmd_con(pmd_cmds(opts))
        stream_configs = [
            [0, 0],
            [0, 1],
            [0, 2],
            [0, 3],
            [0, 4],
            [0, 5],
            [0, 6],
            [0, 7],
        ]
        traffic_tasks = [
            [[0, 1, 2, 3, 4, 5, 6, 7], 100, (7.3, "Gbps", 3)],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks, frame_size=68)
        self.testpmd_close()
        time.sleep(5)
        self.testpmd_start(vfs_grp)
        opts = [
            "add port tm node shaper profile 2 1 1000000 0 100000000 0 0 0",
            "add port tm node shaper profile 2 2 1000000 0 250000000 0 0 0",
            "add port tm node shaper profile 2 3 1000000 0 100000000 0 0 0",
        ]
        self.pmd_con(pmd_cmds(opts))
        traffic_tasks = [
            [[0, 1, 2, 3, 4, 5, 6, 7], 100, (7.3, "Gbps", 3)],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks, frame_size=68)
        self.testpmd_close()
        time.sleep(5)
        self.testpmd_start(vfs_grp)
        opts = [
            "add port tm node shaper profile 2 1 0 0 0 0 0 0",
            "add port tm node shaper profile 2 2 0 0 0 0 0 0",
            "add port tm node shaper profile 2 3 0 0 0 0 0 0",
        ]
        self.pmd_con(pmd_cmds(opts))
        traffic_tasks = [
            [[0, 1, 2, 3, 4, 5, 6, 7], 100, (7.3, "Gbps", 3)],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks, frame_size=68)
        self.testpmd_close()

        expected = [
            ((1, 3), [0], 5),
            ((1, 3), [1], 10),
            ((1, 3), [2], 15),
            ((1, 3), [3], 10),
            ((1, 3), [4], 20),
            ((1, 3), [5], 1),
            ((1, 3), [6], 30),
            ((1, 3), [7], 9),
        ]
        self.check_queue_pkts_ratio(expected, results[-1][2])

    def verify_ets_mode_1_TC(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,0,0,0,0,0,0,0 --tcbw 100,0,0,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0",
            f"{self.dcbgetset} {self.nic25G_intf}  --ieee --up2tc 0,0,0,0,0,0,0,0 --tcbw 100,0,0,0,0,0,0,0 --tsa 2,2,2,2,2,2,2,2 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
            f"ifconfig {self.nic25G_intf} up",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmds = [
            "set portlist 0,2,1,3",
            "show config fwd",
            "port stop all",
            "add port tm node shaper profile 0 1 1000000 0 10000000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 yes", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 900 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 1 yes", self.check_error_output],
            "add port tm node shaper profile 2 1 1000000 0 1000000000 0 0 0",
            "add port tm nonleaf node 2 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 2 900 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 2 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 2 1 900 0 1 2 1 0 0xffffffff 0 0",
            ["port tm hierarchy commit 2 yes", self.check_error_output],
            "add port tm nonleaf node 3 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 3 900 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 3 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 4 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 5 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 6 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 3 7 900 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 3 yes", self.check_error_output],
            "port start all",
            "set fwd mac",
            "start",
        ]
        self.pmd_con(cmds)
        stream_configs = [
            [0, 0],
            [0, 1],
            [0, 2],
            [0, 3],
            [0, 4],
            [0, 5],
            [0, 6],
            [0, 7],
        ]
        traffic_tasks = [
            [[0], 12.5, (7.3, "Gbps", 3)],
            [[0, 1, 2, 3, 4, 5, 6, 7], 100, (7.3, "Gbps", 3)],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks, frame_size=68)
        self.testpmd_close()

    def verify_query_qos_setting(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmds = [
            "port stop all",
            "add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 no", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 700 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 1 no", self.check_error_output],
            "port start all",
        ]
        self.pmd_con(cmds)
        cmds = [
            "show port tm cap 1",
        ]
        self.pmd_con(cmds)
        cmds = [
            "show port tm level cap 1 0",
            "show port tm level cap 1 1",
            "show port tm level cap 1 2",
        ]
        outputs = self.pmd_con(cmds)
        expected = [
            "cap.nonleaf.shaper_private_rate_min 0",
            "cap.nonleaf.shaper_private_rate_max 12500000000",
        ]
        [self.check_output(expected, output) for output in outputs]
        cmds = [
            "show port tm node cap 1 900",
            "show port tm node cap 1 800",
            "show port tm node cap 1 1",
        ]
        outputs = self.pmd_con(cmds)
        expected = [
            [
                "cap.shaper_private_rate_min 1000000",
                "cap.shaper_private_rate_max 2000000",
            ],
            [
                "cap.shaper_private_rate_min 1000000",
                "cap.shaper_private_rate_max 4000000",
            ],
            "node parameter null: not support capability get (error 22)",
        ]
        [
            self.check_output(_expected, output)
            for _expected, output in zip(expected, outputs)
        ]
        cmds = [
            "show port tm node type 1 0",
            "show port tm node type 1 900",
            "show port tm node type 1 1000",
        ]
        outputs = self.pmd_con(cmds)
        expected_types = ["leaf node", "nonleaf node", "nonleaf node"]
        [
            self.check_output(_expected, output)
            for _expected, output in zip(expected_types, outputs)
        ]
        self.testpmd_close()

    def verify_pf_reset(self, vfs_grp):
        self.strict_mode_check_peak_tb_rate_preset(vfs_grp)
        stream_configs = [
            [0, 2],
        ]
        traffic_tasks = [
            [[0], 25, (2, "MBps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks)
        self.testpmd_close()
        pci = str(int(self.nic100g_pci[5:7]) - 1)
        cmds = [
            f"echo 1 > /sys/devices/pci0000:{pci}/0000:{pci}:00.0/{self.nic100g_pci}/reset",
        ]
        self.d_a_con(cmds)
        self.strict_mode_check_peak_tb_rate_preset(vfs_grp, commit_check=False)
        stream_configs = [
            [0, 2],
        ]
        traffic_tasks = [
            [[0], 25, (0, "MBps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks)
        self.testpmd_close()

    def verify_vf_reset(self, vfs_grp):
        cmds = [
            f"ip link set {self.nic100G_intf} vf 1 mac 00:11:22:33:44:66",
        ]
        self.d_a_con(cmds)
        self.strict_mode_check_peak_tb_rate_preset(vfs_grp)
        cmds = [
            "port stop 1",
            "port reset 1",
            "port start 1",
            "start",
        ]
        self.pmd_con(cmds)
        stream_configs = [
            [0, 2, "00:11:22:33:44:66"],
            [0, 5, "00:11:22:33:44:66"],
            [0, 3, "00:11:22:33:44:66"],
            [0, 4, "00:11:22:33:44:66"],
        ]
        traffic_tasks = [
            [[0], 25, (2, "MBps")],
            [[1], 25, (2, "MBps")],
            [[2], 25, (4, "MBps")],
            [[3], 25, (4, "MBps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks)
        self.testpmd_close()
        cmds = [
            f"ip link set {self.nic100G_intf} vf 1 mac 00:11:22:33:44:55",
        ]
        self.d_a_con(cmds)
        self.strict_mode_check_peak_tb_rate_preset(vfs_grp)
        stream_configs = [
            [0, 2],
            [0, 5],
            [0, 3],
            [0, 4],
        ]
        traffic_tasks = [
            [[0], 25, (2, "MBps")],
            [[1], 25, (2, "MBps")],
            [[2], 25, (4, "MBps")],
            [[3], 25, (4, "MBps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks)
        self.testpmd_close()

    def verify_link_status_change(self, vfs_grp):
        cmds = [
            f"ifconfig {self.nic100G_intf} down",
        ]
        self.strict_mode_check_peak_tb_rate_preset(vfs_grp, if_op="down")
        stream_configs = [
            [0, 2],
        ]
        traffic_tasks = [
            [[0], 25, (2, "MBps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks)
        self.testpmd_close()
        cmds = [
            f"ifconfig {self.nic100G_intf} up",
        ]
        self.strict_mode_check_peak_tb_rate_preset(vfs_grp)
        stream_configs = [
            [0, 2],
        ]
        traffic_tasks = [
            [[0], 25, (2, "MBps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks)
        self.testpmd_close()

    def verify_DCB_setting_TC_change(self, vfs_grp):
        cmd = f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,40,50,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0"
        self.strict_mode_check_peak_tb_rate_preset(vfs_grp, dcb_cmd=cmd)
        stream_configs = [
            [0, 2],
            [0, 5],
            [0, 3],
            [0, 4],
        ]
        traffic_tasks = [
            [[0], 25, (2, "MBps")],
            [[1], 25, (2, "MBps")],
            [[2], 25, (4, "MBps")],
            [[3], 25, (4, "MBps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks)
        self.testpmd_close()

        queue_mapping = [
            ((1, 1), range(4)),
            ((1, 1), range(4)),
            ((1, 1), range(4, 6)),
            ((1, 1), range(6, 8)),
        ]
        [
            self.check_queue(expected, real[2])
            for expected, real in zip(queue_mapping, results)
        ]

    def negative_case_for_requested_vf_preset(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,0,0,1,0,0,0,0 --tcbw 20,80,0,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
            f"ip link set dev {self.nic100G_intf} vf 0 trust on",
            f"ip link set {self.nic100G_intf} vf 1 mac 00:11:22:33:44:55",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmd = "port stop all"
        self.pmd_con(cmd)

    def verify_Requested_VF_id_is_valid(self, vfs_grp):
        self.negative_case_for_requested_vf_preset(vfs_grp)
        cmds = [
            "add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 900 0 1 2 1 0 0xffffffff 0 0",
        ]
        outputs = self.pmd_con(cmds)
        expected = "node id: too many VSI for one TC (error 33)"
        self.check_output(expected, outputs[-1])
        self.testpmd_close()

    def verify_Valid_number_of_TCs_for_the_target_VF(self, vfs_grp):
        self.negative_case_for_requested_vf_preset(vfs_grp)
        cmds = [
            "add port tm node shaper profile 0 1 63000 0 12500000000 0 0 0",
            "add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0",
            "port tm hierarchy commit 0 yes",
        ]
        outputs = self.pmd_con(cmds)
        expected = [
            "ice_dcf_commit_check(): Not all enabled TC nodes are set",
            "no error: (no stated reason) (error 0)",
        ]
        self.check_output(expected, outputs[-1])
        cmds = [
            "add port tm node shaper profile 0 1 63000 0 12500000000 0 0 0",
            "add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800000 1000000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800000 0 1 2 2 0 0xffffffff 0 0",
            "port tm hierarchy commit 0 yes",
        ]
        outputs = self.pmd_con(cmds)
        expected = [
            "ice_dcf_commit_check(): Not all VFs are binded to TC1",
            "no error: (no stated reason) (error 0)",
        ]
        self.check_output(expected, outputs[-1])
        cmds = [
            "add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0",
        ]
        outputs = self.pmd_con(cmds)
        expected = (
            "shaper profile id field (node params): shaper profile not exist (error 23)"
        )
        self.check_output(expected, outputs[-1])
        self.testpmd_close()

    def verify_Valid_Min_and_Max_values(self, vfs_grp):
        self.negative_case_for_requested_vf_preset(vfs_grp)
        cmds = [
            "add port tm node shaper profile 0 1 62999 0 2000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0",
            "add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800000 1000000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800000 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800000 0 1 2 2 0 0xffffffff 0 0",
            "port tm hierarchy commit 0 yes",
        ]
        outputs = self.pmd_con(cmds)
        expected = [
            "ice_dcf_execute_virtchnl_cmd(): No response (1 times) or return failure (-5) for cmd 37",
            "ice_dcf_set_vf_bw(): fail to execute command VIRTCHNL_OP_DCF_CONFIG_BW",
            "no error: (no stated reason) (error 0)",
        ]
        self.check_output(expected, outputs[-1])
        self.testpmd_close()
        self.negative_case_for_requested_vf_preset(vfs_grp)
        cmds = [
            "add port tm node shaper profile 0 1 63000 0 2000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0",
            "add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800000 1000000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800000 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800000 0 1 2 2 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 no", self.check_error_output],
        ]
        outputs = self.pmd_con(cmds)
        self.testpmd_close()
        msg = "failed to set commands"
        self.verify(all(["error" not in output.lower() for output in outputs]), msg)
        self.negative_case_for_requested_vf_preset(vfs_grp)
        cmds = [
            "add port tm node shaper profile 0 1 2001000 0 2000000 0 0 0",
            "add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800000 1000000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800000 0 1 2 1 0 0xffffffff 0 0",
            "port tm hierarchy commit 0 yes",
        ]
        outputs = self.pmd_con(cmds)
        expected = [
            "ice_dcf_execute_virtchnl_cmd(): No response (1 times) or return failure (-5) for cmd 37",
            "ice_dcf_set_vf_bw(): fail to execute command VIRTCHNL_OP_DCF_CONFIG_BW",
            "no error: (no stated reason) (error 0)",
        ]
        self.check_output(expected, outputs[-1])
        self.testpmd_close()
        self.negative_case_for_requested_vf_preset(vfs_grp)
        cmds = [
            "add port tm node shaper profile 0 1 2000000 0 2000000 0 0 0",
            "add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800000 1000000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800000 0 1 2 1 0 0xffffffff 0 0",
            "port tm hierarchy commit 0 yes",
        ]
        outputs = self.pmd_con(cmds)
        self.testpmd_close()
        msg = "failed to set commands"
        self.verify(all(["error" not in output.lower() for output in outputs]), msg)
        self.negative_case_for_requested_vf_preset(vfs_grp)
        cmds = [
            "add port tm node shaper profile 0 1 1000000000 0 12000000000 0 0 0",
            "add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800000 1000000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800000 0 1 2 1 0 0xffffffff 0 0",
            "port tm hierarchy commit 0 yes",
        ]
        outputs = self.pmd_con(cmds)
        expected = "ice_dcf_validate_tc_bw(): Total value of TC0 min bandwidth and other TCs' max bandwidth 104000000kbps should be less than port link speed 100000000kbps"
        self.check_output(expected, outputs[-1])
        self.testpmd_close()

    def verify_Valid_Min_and_Max_values_02(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,0,0,1,0,0,0,0 --tcbw 20,80,0,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
            f"ip link set dev {self.nic100G_intf} vf 0 trust on",
            f"ip link set {self.nic100G_intf} vf 1 mac 00:11:22:33:44:55",
            f"ip link set {self.nic100G_intf} vf 2 mac 00:11:22:33:44:66",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmds = [
            "port stop all",
            "add port tm node shaper profile 0 1 10000000 0 1000000000 0 0 0",
            "add port tm node shaper profile 0 2 10000000 0 8500000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 800 0 1 2 2 0 0xffffffff 0 0",
            "port tm hierarchy commit 0 yes",
        ]
        outputs = self.pmd_con(cmds)
        expected = [
            "ice_dcf_validate_tc_bw(): Total value of TC0 min bandwidth and other TCs' max bandwidth 136160000kbps should be less than port link speed 100000000kbps",
            "no error: (no stated reason) (error 0)",
        ]
        self.check_output(expected, outputs[-1])
        self.testpmd_close()

    def verify_Valid_Min_and_Max_values_03(self, vfs_grp):
        self.negative_case_for_requested_vf_preset(vfs_grp)
        cmds = [
            "port stop all",
            "add port tm node shaper profile 0 1 0 0 0 0 0 0",
            "add port tm nonleaf node 0 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800000 1000000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800000 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800000 0 1 2 1 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 yes", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 800 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 1 yes", self.check_error_output],
            "port start all",
            "set fwd mac",
            "start",
        ]
        self.pmd_con(cmds)
        stream_configs = [
            [0, 0],
            [0, 3],
        ]
        traffic_tasks = [
            [[0], 100, (100, "Gbps")],
            [[1], 100, (100, "Gbps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks, frame_size=1024)
        self.testpmd_close()
        queue_mapping = [
            ((1, 1), range(4)),
            ((1, 1), range(4, 8)),
        ]
        [
            self.check_queue(expected, real[2])
            for expected, real in zip(queue_mapping, results)
        ]

    def negative_case_for_req_vf_to_update_its_queue_to_tc_mapping_preset(
        self, vfs_grp
    ):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
            f"ip link set dev {self.nic100G_intf} vf 0 trust on",
            f"ip link set {self.nic100G_intf} vf 1 mac 00:11:22:33:44:55",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmd = "port stop all"
        self.pmd_con(cmd)

    def verify_Total_number_of_queue_pairs_match_to_what_the_VF_is_allocated(
        self, vfs_grp
    ):
        self.negative_case_for_req_vf_to_update_its_queue_to_tc_mapping_preset(vfs_grp)
        cmds = [
            "add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 yes", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0",
            "port tm hierarchy commit 1 yes",
        ]
        outputs = self.pmd_con(cmds)
        expected = [
            "iavf_hierarchy_commit(): queue node is less than allocated queue pairs",
            "no error: (no stated reason) (error 0)",
        ]
        self.check_output(expected, outputs[-1])
        cmds = [
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 8 700 0 1 2 0 0 0xffffffff 0 0",
        ]
        outputs = self.pmd_con(cmds)
        expected = "num strict priorities field (node params): SP priority not supported (error 27)"
        self.check_output(expected, outputs[-1])
        self.testpmd_close()

    def verify_Number_of_TCs_match_is_less_than_TC_enabled_on_the_VF(self, vfs_grp):
        self.negative_case_for_req_vf_to_update_its_queue_to_tc_mapping_preset(vfs_grp)
        cmds = [
            "add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0",
            "port tm hierarchy commit 0 yes",
        ]
        outputs = self.pmd_con(cmds)
        expected = [
            "ice_dcf_commit_check(): Not all VFs are binded to TC2",
            "no error: (no stated reason) (error 0)",
        ]
        self.check_output(expected, outputs[-1])
        cmds = [
            "add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 no", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 800 0 1 2 0 0 0xffffffff 0 0",
            "port tm hierarchy commit 1 yes",
        ]
        outputs = self.pmd_con(cmds)
        expected = [
            "iavf_hierarchy_commit(): Does not set VF vsi nodes to all TCs",
            "no error: (no stated reason) (error 0)",
        ]
        self.check_output(expected, outputs[-1])
        cmds = [
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 800 0 1 2 0 0 0xffffffff 0 0",
            "port tm hierarchy commit 1 yes",
        ]
        outputs = self.pmd_con(cmds)
        msg = "failed to set commands"
        self.verify(all(["error" not in output.lower() for output in outputs]), msg)
        stream_configs = [
            [0, 0],
            [0, 3],
        ]
        traffic_tasks = [
            [[0], 100, (100, "rGbps")],
            [[1], 100, (100, "rGbps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks, frame_size=1024)
        self.testpmd_close()
        queue_mapping = [
            ((1, 1), range(4)),
            ((1, 1), range(4, 8)),
        ]
        [
            self.check_queue(expected, real[2])
            for expected, real in zip(queue_mapping, results)
        ]

    def verify_Number_of_TCs_match_is_more_than_TC_enabled_on_the_VF(self, vfs_grp):
        self.negative_case_for_req_vf_to_update_its_queue_to_tc_mapping_preset(vfs_grp)
        cmds = [
            "add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 600 1000 0 1 1 -1 1 0 0",
        ]
        outputs = self.pmd_con(cmds)
        expected = "node id: too many TCs (error 33)"
        self.check_output(expected, outputs[-1])
        cmds = [
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 6 600 0 1 2 2 0 0xffffffff 0 0",
        ]
        outputs = self.pmd_con(cmds)
        expected = "parent node id: parent not exist (error 19)"
        self.check_output(expected, outputs[-1])
        cmds = [
            ["port tm hierarchy commit 0 yes", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 600 1000 0 1 1 0 1 0 0",
        ]
        outputs = self.pmd_con(cmds)
        expected = "node id: too many TCs (error 33)"
        self.check_output(expected, outputs[-1])
        cmds = [
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 600 0 1 2 0 0 0xffffffff 0 0",
        ]
        outputs = self.pmd_con(cmds)
        expected = "parent node id: parent not exist (error 19)"
        self.check_output(expected, outputs[-1])
        self.testpmd_close()

    def verify_overlap_between_queue_to_TC_mapping(self, vfs_grp):
        self.negative_case_for_req_vf_to_update_its_queue_to_tc_mapping_preset(vfs_grp)
        cmds = [
            "add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 no", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 800 0 1 2 0 0 0xffffffff 0 0",
        ]
        outputs = self.pmd_con(cmds)
        expected = "node id: node id already used (error 33)"
        self.check_output(expected, outputs[-1])
        self.testpmd_close()

    def verify_Non_contiguous_TC_setting_in_queue_mapping(self, vfs_grp):
        self.negative_case_for_req_vf_to_update_its_queue_to_tc_mapping_preset(vfs_grp)
        cmds = [
            "add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 yes", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 800 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 1 yes", self.check_error_output],
            "port start all",
            "set fwd mac",
            "start",
        ]
        self.pmd_con(cmds)
        stream_configs = [
            [0, 2],
            [0, 5],
            [0, 3],
            [0, 4],
        ]
        traffic_tasks = [
            [[0, 1], 100, (2, "MBps")],
            [[2], 25, (4, "MBps")],
            [[3], 25, (4, "MBps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks, frame_size=68)
        self.testpmd_close()
        queue_mapping = [
            ((1, 1), range(2)),
            ((1, 1), range(2, 4)),
            ((1, 1), range(4, 8)),
        ]
        [
            self.check_queue(expected, real[2])
            for expected, real in zip(queue_mapping, results)
        ]

    def verify_different_vlan_ID(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf}  --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        cmds = [
            "port stop all",
            "vlan set filter on 1",
            "rx_vlan add 1 1",
            "rx_vlan add 2 1",
            "add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0",
            ["port tm hierarchy commit 0 no", self.check_error_output],
            "add port tm nonleaf node 1 1000 -1 0 1 0 0 1 0 0",
            "add port tm nonleaf node 1 900 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 800 1000 0 1 1 0 1 0 0",
            "add port tm nonleaf node 1 700 1000 0 1 1 0 1 0 0",
            "add port tm leaf node 1 0 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 1 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 2 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 3 900 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 4 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 5 800 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 6 700 0 1 2 0 0 0xffffffff 0 0",
            "add port tm leaf node 1 7 700 0 1 2 0 0 0xffffffff 0 0",
            ["port tm hierarchy commit 1 no", self.check_error_output],
            "port start all",
            "set fwd mac",
            "start",
        ]
        self.pmd_con(cmds)
        stream_configs = [
            [0, 0],
            [0, 1],
            [0, 3],
            [0, 4],
            [1, 0],
            [1, 3],
            [2, 2],
            [2, 4],
        ]
        traffic_tasks = [
            [[0, 1, 4, 6], 100, (2, "MBps")],
            [[2, 5], 25, (4, "MBps")],
            [[3, 7], 25, (4, "MBps")],
            [[0, 1, 2, 3, 4, 5, 6, 7], 100, (10, "MBps")],
        ]
        results = self.check_traffic(stream_configs, traffic_tasks, frame_size=1024)
        self.testpmd_close()
        queue_mapping = [
            ((1, 1), range(4)),
            ((1, 1), range(4, 6)),
            ((1, 1), range(6, 8)),
            None,
        ]
        [
            self.check_queue(expected, real[2])
            for expected, real in zip(queue_mapping, results)
        ]

    def verify_delete_qos_setting(self, vfs_grp):
        cmds = [
            f"{self.dcbgetset} {self.nic100G_intf} --ieee --up2tc 0,0,0,1,2,0,0,0 --tcbw 10,30,60,0,0,0,0,0 --tsa 0,0,0,0,0,0,0,0 --pfc 0,0,0,0,0,0,0,0",
            f"ifconfig {self.nic100G_intf} up",
        ]
        self.d_a_con(cmds)
        self.testpmd_start(vfs_grp)
        step2_cmds = [
            "port stop all",
            "add port tm node shaper profile 0 1 1000000 0 2000000 0 0 0",
            "add port tm node shaper profile 0 2 1000000 0 4000000 0 0 0",
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 800 1000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node 0 700 1000 0 1 1 -1 1 0 0",
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0",
            "add port tm leaf node 0 2 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 3 800 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 4 700 0 1 2 2 0 0xffffffff 0 0",
            "add port tm leaf node 0 5 700 0 1 2 2 0 0xffffffff 0 0",
        ]
        self.pmd_con(step2_cmds)

        cmd = "del port tm node 0 1000"
        output = self.pmd_con(cmd)
        expected = [
            "node id: cannot delete a node which has children (error 33)",
        ]
        self.check_output(expected, output)

        cmd = "del port tm node 0 700"
        output = self.pmd_con(cmd)
        expected = [
            "node id: cannot delete a node which has children (error 33)",
        ]
        self.check_output(expected, output)

        cmd = "del port tm node shaper profile 0 1"
        output = self.pmd_con(cmd)
        expected = [
            "shaper profile null: profile in use (error 10)",
        ]
        self.check_output(expected, output)

        cmds = [
            "del port tm node 0 5",
            "del port tm node 0 4",
            "del port tm node 0 3",
            "del port tm node 0 2",
            "del port tm node 0 1",
            "del port tm node 0 0",
            "del port tm node 0 700",
            "del port tm node 0 800",
            "del port tm node 0 900",
            "del port tm node 0 1000",
            "del port tm node shaper profile 0 1",
            "del port tm node shaper profile 0 2",
        ]
        outputs = self.pmd_con(cmds)
        msg = "failed to set commands"
        self.verify(all(["error" not in output.lower() for output in outputs]), msg)

        self.pmd_con(step2_cmds)
        cmd = "port tm hierarchy commit 0 no"
        self.pmd_con(cmd)
        cmd = "del port tm node 0 5"
        output = self.pmd_con(cmd)
        expected = [
            "cause unspecified: already committed (error 1)",
        ]
        self.check_output(expected, output)

        self.testpmd_close()

    def suite_init(self):
        self.dcbgetset = "dcbgetset"
        self.pf_preset()
        self.vf_init()
        self.testpmd_init()
        self.pmd_stat = None

    #
    # Test cases.
    #
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.suite_init()

    def tear_down_all(self):
        """
        Run after each test suite.
        """

    def set_up(self):
        """
        Run before each test case.
        """

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        self.pf_restore()

    def test_perf_strict_mode_check_peak_tb_rate(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_strict_mode_check_peak_tb_rate(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_ets_mode_check_peak_tb_rate(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g, self.nic_25g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_ets_mode_check_peak_tb_rate(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_strict_mode_check_cmit_tb_rate(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g, self.nic_25g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_strict_mode_check_cmit_tb_rate(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_ets_mode_check_TC_throughput_min_BW_allocation(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g, self.nic_25g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_ets_mode_check_TC_throughput_min_BW_allocation(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_iavf_VFs_strict_mode_check_peak_tb_rate(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 3])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_iavf_VFs_strict_mode_check_peak_tb_rate(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_iavf_VFs_strict_mode_check_cmit_tb_rate(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g, self.nic_25g], 3])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_iavf_VFs_strict_mode_check_cmit_tb_rate(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_iavf_VFs_ets_mode(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g, self.nic_25g], 3])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_iavf_VFs_ets_mode(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_strict_mode_8_TCs(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_strict_mode_8_TCs(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_strict_mode_1_TC(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_strict_mode_1_TC(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_ets_mode_8_TCs(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g, self.nic_25g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_ets_mode_8_TCs(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_ets_mode_1_TC(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g, self.nic_25g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_ets_mode_1_TC(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_query_qos_setting(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_query_qos_setting(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_pf_reset(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_pf_reset(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_vf_reset(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_vf_reset(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_link_status_change(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_link_status_change(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_DCB_setting_TC_change(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_DCB_setting_TC_change(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_Requested_VF_id_is_valid(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_Requested_VF_id_is_valid(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_Valid_number_of_TCs_for_the_target_VF(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_Valid_number_of_TCs_for_the_target_VF(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_Valid_Min_and_Max_values(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_Valid_Min_and_Max_values(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

        try:
            self.vf_create(*[[self.nic_100g], 3])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_Valid_Min_and_Max_values_02(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_Valid_Min_and_Max_values_03(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_Total_number_of_queue_pairs_match_to_what_the_VF_is_allocated(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_Total_number_of_queue_pairs_match_to_what_the_VF_is_allocated(
                vfs_group
            )
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_Number_of_TCs_match_is_less_than_TC_enabled_on_the_VF(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_Number_of_TCs_match_is_less_than_TC_enabled_on_the_VF(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_Number_of_TCs_match_is_more_than_TC_enabled_on_the_VF(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_Number_of_TCs_match_is_more_than_TC_enabled_on_the_VF(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_overlap_between_queue_to_TC_mapping(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_overlap_between_queue_to_TC_mapping(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_Non_contiguous_TC_setting_in_queue_mapping(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_Non_contiguous_TC_setting_in_queue_mapping(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_different_vlan_ID(self):
        except_content = None
        try:
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_different_vlan_ID(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()
        if except_content:
            raise VerifyFailure(except_content)

    def test_perf_delete_qos_setting(self):
        except_content = None
        try:
            self.vf_init()
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_delete_qos_setting(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()

        try:
            self.pf_preset(num=1)
            self.vf_init()
            self.vf_create(*[[self.nic_100g], 2])
            vfs_group = [info.get("vfs_pci") for _, info in self.vf_ports_info.items()]
            self.verify_delete_qos_setting(vfs_group)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.testpmd_close()
            self.vf_destroy()

        self.pf_preset()
        self.vf_init()

        if except_content:
            raise VerifyFailure(except_content)
