# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2023 Intel Corporation
#
"""
DPDK Test suite.
ICE Enable basic HQoS on PF driver.
"""

import re
import time
from copy import deepcopy
from pprint import pformat

from framework.packet import Packet
from framework.pktgen import TRANSMIT_CONT
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE, get_nic_name
from framework.test_case import TestCase

PKT_LEN = [64, 128, 256, 512, 1024, 1518, 512, 1024]
STREAM_UP_CONFIG = [0, 1, 2, 0, 0, 0, 0, 0]
LINERATE = 100


class TestIceEnableBasicHqosOnPF(TestCase):
    def set_up_all(self):
        self.dut_ports = self.dut.get_ports()
        # for test topo requirement,need 1 100G port and 1 25G port
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        "test topo is port 0 is 100G-E810C and port 1 is 25G-E810"
        self.skip_case(
            self.check_require_nic_for_test(),
            "Topology is ICE_100G-E810C_QSFP and ICE_25G-E810_XXV_SFP",
        )
        # get the nic port id
        self.get_require_nic_port_id()
        self.cores = "1S/9C/1T"
        # check core num
        core_list = self.dut.get_core_list(self.cores)
        self.port_sockets = self.dut.get_numa_id(self.ice_100G_port_id)
        self.verify(len(core_list) >= 9, "Insufficient cores for testing")
        self.tester_port0 = self.tester.get_local_port(self.ice_100G_port_id)
        self.tester_port1 = self.tester.get_local_port(self.ice_25G_port_id)
        self.ice_100G_port_mac = self.dut.get_mac_address(self.ice_100G_port_id)

        self.pmd_output = PmdOutput(self.dut)

    def get_nic_info_from_ports_cfg(self):
        """
        get port.cfg nic type/intf/pci list
        :return: port config nic list
        """
        nic_list = []
        for id in self.dut.get_ports():
            nic_dict = {}
            for info in ["port_id", "type", "intf", "pci"]:
                if info == "port_id":
                    nic_dict[info] = id
                    continue
                nic_dict[info] = self.dut.ports_info[id][info]
                if info == "type":
                    nic_dict["name"] = get_nic_name(nic_dict[info])
            nic_list.append(nic_dict)
        return nic_list

    def check_require_nic_for_test(self):
        """
        check the port is E810_100G and E810_25G
        :return: check status, True or False
        """
        for id, _nic in enumerate(self.get_nic_info_from_ports_cfg()):
            if _nic["name"] not in ["ICE_100G-E810C_QSFP", "ICE_25G-E810_XXV_SFP"]:
                return False
        return True

    def get_require_nic_port_id(self):
        """
        get the nic port id
        :return: 100G port id and 25G port id
        """
        nic_list = self.get_nic_info_from_ports_cfg()
        for nic in nic_list:
            if nic["name"] == "ICE_100G-E810C_QSFP":
                self.ice_100G_port_id = nic["port_id"]
            elif nic["name"] == "ICE_25G-E810_XXV_SFP":
                self.ice_25G_port_id = nic["port_id"]
            else:
                raise Exception("unsupport nic for test require")

    def launch_testpmd(self, param=""):
        """
        start testpmd and check testpmd link status
        :param param: rxq/txq
        """
        self.pmd_output.start_testpmd(
            cores=self.cores, socket=self.port_sockets, param=param
        )
        res = self.pmd_output.wait_link_status_up("all", timeout=15)
        self.verify(res is True, "there have port link is down")
        self.testpmd_flag = True

    def close_testpmd(self):
        """
        close testpmd
        """
        if not self.testpmd_flag:
            return
        try:
            self.pmd_output.quit()
        except Exception as e:
            self.logger.error("The testpmd status is incorrect")
        self.testpmd_flag = False

    def get_queue_packets_stats(self, port):
        """
        get testpmd tx pkts stats
        :param port: tx port
        :return: pkts list
        """
        output = self.pmd_output.execute_cmd("stop")
        time.sleep(3)
        self.pmd_output.execute_cmd("start")
        p = re.compile("TX Port= %d/Queue=.*\n.*TX-packets: ([0-9]+)\s" % port)
        tx_pkts = list(map(int, p.findall(output)))
        return tx_pkts

    def add_stream_to_pktgen(self, txport, rxport, send_pkts, option):
        """
        add streams to pktgen and return streams id
        """
        stream_ids = []
        for pkt in send_pkts:
            _option = deepcopy(option)
            _option["pcap"] = pkt
            stream_id = self.tester.pktgen.add_stream(txport, rxport, pkt)
            self.tester.pktgen.config_stream(stream_id, _option)
            stream_ids.append(stream_id)
        return stream_ids

    def config_stream(self, fields, frame_size):
        """
        config stream and return pkt
        """
        pri = fields
        pkt_config = {
            "type": "VLAN_UDP",
            "pkt_layers": {
                "ether": {"dst": self.ice_100G_port_mac},
                "vlan": {"vlan": 0, "prio": pri},
                "raw": {"payload": ["58"] * self.get_pkt_len(frame_size)},
            },
        }
        pkt_type = pkt_config.get("type")
        pkt_layers = pkt_config.get("pkt_layers")
        pkt = Packet(pkt_type=pkt_type)
        for layer in list(pkt_layers.keys()):
            pkt.config_layer(layer, pkt_layers[layer])
        return pkt.pktgen.pkt

    def testpmd_query_stats(self):
        """
        traffic callback function, return port stats
        """
        time.sleep(3)
        output = self.pmd_output.execute_cmd(
            "show port stats {}".format(self.ice_25G_port_id)
        )
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

    def get_pkt_len(self, frame_size):
        HEADER_SIZE["vlan"] = 4
        headers_size = sum([HEADER_SIZE[x] for x in ["eth", "ip", "vlan", "udp"]])
        pktlen = frame_size - headers_size
        return pktlen

    def start_traffic(self, pkt_list):
        """
        send stream and return results
        """
        self.tester.pktgen.clear_streams()
        duration = 20
        s_option = {
            "stream_config": {
                "txmode": {},
                "transmit_mode": TRANSMIT_CONT,
                "rate": LINERATE,
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
        stream_ids = self.add_stream_to_pktgen(
            self.tester_port0, self.tester_port0, pkt_list, s_option
        )
        traffic_opt = {
            "method": "throughput",
            "duration": duration,
            "interval": duration - 5,
            "callback": self.testpmd_query_stats,
        }
        time.sleep(3)
        result = self.tester.pktgen.measure(stream_ids, traffic_opt)
        return result

    def get_traffic_results(self):
        """
        get traffic results, append results, port stats, queue stats
        """
        pkt_list = []
        results = []
        for id in range(len(STREAM_UP_CONFIG)):
            pkt = self.config_stream(STREAM_UP_CONFIG[id], frame_size=PKT_LEN[id])
            pkt_list.append(pkt)
        result = self.start_traffic(pkt_list)
        queue_stats = self.get_queue_packets_stats(self.ice_25G_port_id)
        results.append([result, self.pmd_stat, queue_stats])
        return results

    def check_traffic_throughput(self, expect_results, rel_results):
        """
        compare traffic throughput with expect results
        """
        status = False
        # the nic speed can limit the throughout is 10G
        limit_bps = 10
        tx_bps = 0
        for traffic_task, _result in zip(expect_results, rel_results):
            _expected, unit, port = traffic_task
            _, pmd_stat, _ = _result
            real_stat = pmd_stat.get(f"port {port}", {})
            real_bps = real_stat.get("tx_bps")
            # check the real bps is between the expect value and the limit value
            if unit == "MBps":
                status = _expected <= (real_bps / 8 / 1e6) < (limit_bps / 8 / 1e6)
            elif unit in ["Gbps", "rGbps"]:
                status = _expected <= (real_bps / 1e9) < limit_bps
            self.logger.info("the real bps is <{}>".format(real_bps))
            msg = (
                f"{pformat(traffic_task)}"
                " not get expected throughput value, real is: "
                f"{pformat(pmd_stat)}"
            )
            self.verify(status, msg)
            tx_bps = real_bps
        return tx_bps

    def check_queue_throughout(self, result, queue_throughout):
        """
        check the per queue throughout.
        "-1" to check a liitle throughout
        """
        status = False
        for _result in result:
            _, pmd_stat, queue_stats = _result
            """
            get the tx_bps
            """
            tx_bps = pmd_stat.get(f"port {self.ice_25G_port_id}").get("tx_bps")
            for _queue_throughout in queue_throughout:
                bias = 10
                sum_queue_stats = 0
                # for check the rest throughout, the value is rough value, set bias=20
                if _queue_throughout[-1] == "rest":
                    queue_id, value, unit, rest = _queue_throughout
                    bias = 20
                else:
                    queue_id, value, unit = _queue_throughout
                if not isinstance(queue_id, list):
                    queue_id = [queue_id]
                total_real_pkts = sum(queue_stats)
                # if value is -1, check the queue has a little throughout,the throughout is less than 1Mbps
                if value == -1:
                    for _queue_id in queue_id:
                        sum_queue_stats += queue_stats[_queue_id]
                    little_throughout = sum_queue_stats / total_real_pkts * tx_bps
                    self.verify(
                        little_throughout / 1e6 < 1,
                        "The throughput of queue is limited to little throughout",
                    )
                    self.logger.info(
                        "check the queue {} throughout < 1Mbps".format(queue_id)
                    )
                    continue
                """
                queue pkts num / total * tx_bps，get the per queue bps
                """
                for _queue_id in queue_id:
                    sum_queue_stats += queue_stats[_queue_id]
                per_queue_throughout = sum_queue_stats / total_real_pkts * tx_bps
                self.logger.info(
                    "queue {} throughout: {}".format(queue_id, per_queue_throughout)
                )
                if unit == "MBps":
                    status = (
                        abs((per_queue_throughout / 8 / 1e6 - value) * 100 / value)
                        < bias
                    )
                elif unit == "Mbps":
                    status = (
                        abs(((per_queue_throughout / 1e6 - value) * 100 / value)) < bias
                    )
                elif unit in ["Gbps", "rGbps"]:
                    status = (
                        abs(((per_queue_throughout / 1e9 - value) * 100 / value)) < bias
                    )
                msg = (
                    f"{pformat(value)}"
                    " not get expected queue throughput value, real is: "
                    f"{pformat(per_queue_throughout)}"
                )
                self.verify(status, msg)

    def check_queue_ratio(self, result, expected, **kwargs):
        """
        check the queue ratio
        :param result: get the throughout result
        :param expected: set the expected ratio
        :param kwargs:
            check_group: if need to check queue group ratio, set check_group is true
        """
        bias = 10
        check_results = []
        check_group = kwargs.get("check_group")
        """
        according to expected, split queue list, retrun queue list and group list
        """
        queues, queue_groups = self.get_pkts_num_list(
            result, expected, check_group=check_group
        )
        for id_queue, queue in enumerate(queues):
            """
            if check queue group ratio, take the group list into queue list
            """
            if check_group:
                queue.append(queue_groups[id_queue])
            for id_ex, ex in enumerate(expected):
                """
                if the ratio is 0, no need to check queue ratio
                """
                if not any(ex):
                    self.logger.info(
                        "check the queue throughout, no need to test ratio"
                    )
                    continue
                new_queue = []
                new_ex = []
                """
                if some queue ratio is 0, no need to check this queue ratio.
                but the queue pkts num will impact the ratio, so remove ratio is 0 in queue list and expect list
                """
                for _ex, _queue in zip(ex, queue[id_ex]):
                    if _ex != 0:
                        new_queue.append(_queue)
                        new_ex.append(_ex)
                total_real_pkts = sum(new_queue)
                expect_total_ratio = sum(new_ex)
                ratio = []
                """
                the ratio of the number of queues is equal to the ratio of queue througout
                """
                for queue_stat in new_queue:
                    real_percentage = queue_stat / total_real_pkts * 100
                    ratio.append(real_percentage)
                self.logger.info("************expected [{}]************".format(id_ex))
                """
                check the real ratio and expect ratio
                """
                for id, percentage in enumerate(new_ex):
                    expect_ratio = percentage / expect_total_ratio * 100
                    _bias = abs(ratio[id] - expect_ratio) / expect_ratio * 100
                    if _bias < bias:
                        self.logger.info(
                            "ratio and expect_ratio:{}".format(
                                (ratio[id], expect_ratio)
                            )
                        )
                        check_results.append(True)
                        continue
                    else:
                        self.logger.error(
                            "can not get expected queue ratio, ratio and expect_ratio:{}".format(
                                (ratio[id], expect_ratio)
                            )
                        )
                        check_results.append(False)
        self.verify(all(check_results), "can not get expected queue ratio")

    def get_pkts_num_list(self, result, expected, **kwargs):
        """
        get pkts num list, according to the expect to split queue num list
        results = [1, 2, 3, 4]
        expect = [[1, 1], [1, 1]]
        return [[1, 2], [3, 4]]
        """
        queue_pkts_num_list = []
        group_pkts_num_list = []
        check_group = kwargs.get("check_group")

        for _result in result:
            ratio_list = []
            for expect_list in expected:
                ratio_list.append(len(expect_list))
            """
            if check_group, the group ratio impact queue num list split, so remove it
            """
            if check_group:
                ratio_list.pop()
            group_throughput = []
            _, _, queue_stats = _result
            queue_iter = iter(queue_stats)
            group_list = [[next(queue_iter) for _ in range(i)] for i in ratio_list]
            queue_pkts_num_list.append(group_list)
            for queue_group in group_list:
                group_throughput.append(sum(queue_group))
            group_pkts_num_list.append(group_throughput)
        return queue_pkts_num_list, group_pkts_num_list

    def test_perf_queuegroup_RR_queue_WFQ_RR_nolimit(self):

        self.launch_testpmd(param="--rxq=8 --txq=8")
        cmds = [
            "add port tm node shaper profile {} 1 100000000 0 100000000 0 0 0",
            "add port tm nonleaf node {} 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node {} 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node {} 800000 900000 0 1 2 -1 1 0 0",
            "add port tm nonleaf node {} 700000 800000 0 1 3 -1 1 0 0",
            "add port tm nonleaf node {} 600000 800000 0 1 3 -1 1 0 0",
            "add port tm leaf node {} 0 700000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 1 700000 0 2 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 2 700000 0 3 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 3 700000 0 4 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 4 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 5 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 6 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 7 600000 0 1 4 -1 0 0xffffffff 0 0",
            "port tm hierarchy commit {} no",
        ]
        for cmd in cmds:
            cmd = cmd.format(self.ice_25G_port_id)
            self.pmd_output.execute_cmd(cmd)
        self.pmd_output.execute_cmd("start")

        traffic_tasks = [
            [8.25, "Gbps", self.ice_25G_port_id],
        ]
        results = self.get_traffic_results()
        self.check_traffic_throughput(traffic_tasks, results)
        expected = [[1, 2, 3, 4], [1, 1, 1, 1], [1, 1]]
        self.check_queue_ratio(results, expected, check_group=True)

    def test_perf_queuegroup_SP_queue_WFQ_RR_nolimit(self):

        self.launch_testpmd(param="--rxq=8 --txq=8")
        cmds = [
            "add port tm node shaper profile {} 1 100000000 0 100000000 0 0 0",
            "add port tm nonleaf node {} 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node {} 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node {} 800000 900000 0 1 2 -1 1 0 0",
            "add port tm nonleaf node {} 700000 800000 0 1 3 -1 1 0 0",
            "add port tm nonleaf node {} 600000 800000 1 1 3 -1 1 0 0",
            "add port tm leaf node {} 0 700000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 1 700000 0 2 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 2 700000 0 3 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 3 700000 0 4 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 4 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 5 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 6 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 7 600000 0 1 4 -1 0 0xffffffff 0 0",
            "port tm hierarchy commit {} no",
            "start",
        ]
        for cmd in cmds:
            cmd = cmd.format(self.ice_25G_port_id)
            self.pmd_output.execute_cmd(cmd)
        self.pmd_output.execute_cmd("start")

        traffic_tasks = [
            [8.25, "Gbps", self.ice_25G_port_id],
        ]
        results = self.get_traffic_results()
        self.check_traffic_throughput(traffic_tasks, results)
        expected = [[1, 2, 3, 4], [0, 0, 0, 0]]
        expected_queue = [
            [4, -1, "Gbps"],
            [5, -1, "Gbps"],
            [6, -1, "Gbps"],
            [7, -1, "Gbps"],
        ]
        self.check_queue_throughout(results, expected_queue)
        self.check_queue_ratio(results, expected)

    def test_perf_queuegroup_RR_queue_WFQ_RR(self):

        self.launch_testpmd(param="--rxq=8 --txq=8")
        cmds = [
            "add port tm node shaper profile {} 1 300000000 0 300000000 0 0 0",
            "add port tm nonleaf node {} 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node {} 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node {} 800000 900000 0 1 2 -1 1 0 0",
            "add port tm nonleaf node {} 700000 800000 0 1 3 -1 1 0 0",
            "add port tm nonleaf node {} 600000 800000 0 1 3 1 1 0 0",
            "add port tm leaf node {} 0 700000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 1 700000 0 2 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 2 700000 0 3 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 3 700000 0 4 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 4 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 5 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 6 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 7 600000 0 1 4 -1 0 0xffffffff 0 0",
            "port tm hierarchy commit {} no",
            "start",
        ]
        for cmd in cmds:
            cmd = cmd.format(self.ice_25G_port_id)
            self.pmd_output.execute_cmd(cmd)
        self.pmd_output.execute_cmd("start")

        traffic_tasks = [
            [8.25, "Gbps", self.ice_25G_port_id],
        ]
        results = self.get_traffic_results()
        self.check_traffic_throughput(traffic_tasks, results)
        expected = [[1, 2, 3, 4], [1, 1, 1, 1]]
        expected_queue = [
            [[4, 5, 6, 7], 2.4, "Gbps"],
        ]
        self.check_queue_throughout(results, expected_queue)
        self.check_queue_ratio(results, expected)

    def test_perf_queuegroup_SP_queue_WFQ_SP(self):

        self.launch_testpmd(param="--rxq=12 --txq=12")
        cmds = [
            "add port tm node shaper profile {} 1 300 0 300000000 0 0 0",
            "add port tm node shaper profile {} 2 300 0 100000000 0 0 0",
            "add port tm node shaper profile {} 3 300 0 10000000 0 0 0",
            "add port tm node shaper profile {} 4 300 0 20000000 0 0 0",
            "add port tm node shaper profile {} 5 200 0 400000000 0 0 0",
            "add port tm nonleaf node {} 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node {} 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node {} 800000 900000 0 1 2 -1 1 0 0",
            "add port tm nonleaf node {} 700000 800000 0 1 3 1 1 0 0",
            "add port tm nonleaf node {} 600000 800000 7 1 3 -1 1 0 0",
            "add port tm leaf node {} 0 700000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 1 700000 0 2 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 2 700000 0 3 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 3 700000 0 4 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 4 600000 0 1 4 3 0 0xffffffff 0 0",
            "add port tm leaf node {} 5 600000 2 1 4 3 0 0xffffffff 0 0",
            "add port tm leaf node {} 6 600000 1 1 4 2 0 0xffffffff 0 0",
            "add port tm leaf node {} 7 600000 2 1 4 4 0 0xffffffff 0 0",
            "add port tm leaf node {} 8 600000 3 1 4 1 0 0xffffffff 0 0",
            "add port tm leaf node {} 9 600000 3 1 4 5 0 0xffffffff 0 0",
            "add port tm leaf node {} 10 600000 5 1 4 3 0 0xffffffff 0 0",
            "add port tm leaf node {} 11 600000 7 1 4 3 0 0xffffffff 0 0",
            "port tm hierarchy commit {} no",
        ]
        for cmd in cmds:
            cmd = cmd.format(self.ice_25G_port_id)
            self.pmd_output.execute_cmd(cmd)
        self.pmd_output.execute_cmd("start")

        traffic_tasks = [
            [8.25, "Gbps", self.ice_25G_port_id],
        ]
        results = self.get_traffic_results()
        real_bps = self.check_traffic_throughput(traffic_tasks, results)
        expected = [[1, 2, 3, 4], [0, 0, 0, 0, 0, 0, 0, 0]]
        expected_queue = [
            [[0, 1, 2, 3], 2.4, "Gbps"],
            [4, 80, "Mbps"],
            [5, 80, "Mbps"],
            [6, 800, "Mbps"],
            [7, 160, "Mbps"],
            [
                8,
                ((real_bps / 1e9 - 2.4) * 1e3 - 80 - 80 - 800 - 160) / 2,
                "Mbps",
                "rest",
            ],
            [
                9,
                ((real_bps / 1e9 - 2.4) * 1e3 - 80 - 80 - 800 - 160) / 2,
                "Mbps",
                "rest",
            ],
            [10, -1, "Mbps"],
            [11, -1, "Mbps"],
        ]
        self.check_queue_throughout(results, expected_queue)
        self.check_queue_ratio(results, expected)

    def test_perf_queuegroup_RR_queue_RR_SP_WFQ(self):

        self.launch_testpmd(param="--rxq=16 --txq=16")
        cmds = [
            "add port tm node shaper profile {} 1 300 0 300000000 0 0 0",
            "add port tm node shaper profile {} 2 100 0 100000000 0 0 0",
            "add port tm nonleaf node {} 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node {} 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node {} 800000 900000 0 1 2 -1 1 0 0",
            "add port tm nonleaf node {} 700000 800000 0 1 3 -1 1 0 0",
            "add port tm nonleaf node {} 600000 800000 0 1 3 -1 1 0 0",
            "add port tm nonleaf node {} 500000 800000 0 1 3 -1 1 0 0",
            "add port tm leaf node {} 0 700000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 1 700000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 2 700000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 3 700000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 4 600000 0 1 4 2 0 0xffffffff 0 0",
            "add port tm leaf node {} 5 600000 4 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 6 600000 1 1 4 1 0 0xffffffff 0 0",
            "add port tm leaf node {} 7 600000 7 1 4 2 0 0xffffffff 0 0",
            "add port tm leaf node {} 8 500000 0 4 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 9 500000 0 2 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 10 500000 0 2 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 11 500000 0 100 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 12 500000 0 3 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 13 500000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 14 500000 0 5 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 15 500000 0 7 4 -1 0 0xffffffff 0 0",
            "port tm hierarchy commit {} no",
        ]
        for cmd in cmds:
            cmd = cmd.format(self.ice_25G_port_id)
            self.pmd_output.execute_cmd(cmd)
        self.pmd_output.execute_cmd("start")

        traffic_tasks = [
            [8.25, "Gbps", self.ice_25G_port_id],
        ]
        results = self.get_traffic_results()
        real_bps = self.check_traffic_throughput(traffic_tasks, results)
        expected = [[1, 1, 1, 1], [0, 0, 0, 0], [4, 2, 2, 100, 3, 1, 5, 7], [1, 1, 1]]
        expected_queue = [
            [4, 800, "Mbps"],
            [5, -1, "Mbps"],
            [6, real_bps / 3 / 1e6 - 800, "Mbps", "rest"],
            [7, -1, "Mbps"],
        ]
        self.check_queue_throughout(results, expected_queue)
        self.check_queue_ratio(results, expected, check_group=True)

    def test_perf_queuegroup_SP_queue_RR_SP_WFQ(self):

        self.launch_testpmd(param="--rxq=16 --txq=16")
        cmds = [
            "add port tm node shaper profile {} 1 300 0 300000000 0 0 0",
            "add port tm node shaper profile {} 2 100 0 100000000 0 0 0",
            "add port tm nonleaf node {} 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node {} 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node {} 800000 900000 0 1 2 -1 1 0 0",
            "add port tm nonleaf node {} 700000 800000 0 1 3 2 1 0 0",
            "add port tm nonleaf node {} 600000 800000 1 1 3 2 1 0 0",
            "add port tm nonleaf node {} 500000 800000 2 1 3 1 1 0 0",
            "add port tm leaf node {} 0 700000 0 1 4 1 0 0xffffffff 0 0",
            "add port tm leaf node {} 1 700000 0 1 4 1 0 0xffffffff 0 0",
            "add port tm leaf node {} 2 700000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 3 700000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 4 600000 0 1 4 1 0 0xffffffff 0 0",
            "add port tm leaf node {} 5 600000 4 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 6 600000 1 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 7 600000 7 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 8 500000 0 4 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 9 500000 0 2 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 10 500000 0 2 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 11 500000 0 100 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 12 500000 0 3 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 13 500000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 14 500000 0 5 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 15 500000 0 7 4 -1 0 0xffffffff 0 0",
            "port tm hierarchy commit {} no",
        ]
        for cmd in cmds:
            cmd = cmd.format(self.ice_25G_port_id)
            self.pmd_output.execute_cmd(cmd)
        self.pmd_output.execute_cmd("start")

        traffic_tasks = [
            [4, "Gbps", self.ice_25G_port_id],
        ]
        results = self.get_traffic_results()
        self.check_traffic_throughput(traffic_tasks, results)
        expected = [[1, 1, 1, 1], [0, 0, 0, 0], [4, 2, 2, 100, 3, 1, 5, 7], [1, 1, 3]]
        expected_queue = [
            [4, 800, "Mbps"],
            [5, -1, "Mbps"],
            [6, -1, "Mbps"],
            [7, -1, "Mbps"],
        ]
        self.check_queue_throughout(results, expected_queue)
        self.check_queue_ratio(results, expected, check_group=True)

    def test_perf_queuegroup_RR_queue_WFQ_WFQ(self):

        self.launch_testpmd(param="--rxq=8 --txq=8")
        cmds = [
            "add port tm node shaper profile {} 1 10000000 0 10000000 0 0 0",
            "add port tm node shaper profile {} 2 20000000 0 20000000 0 0 0",
            "add port tm node shaper profile {} 3 30000000 0 30000000 0 0 0",
            "add port tm node shaper profile {} 4 40000000 0 40000000 0 0 0",
            "add port tm nonleaf node {} 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node {} 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node {} 800000 900000 0 1 2 -1 1 0 0",
            "add port tm nonleaf node {} 700000 800000 0 1 3 -1 1 0 0",
            "add port tm nonleaf node {} 600000 800000 0 1 3 -1 1 0 0",
            "add port tm leaf node {} 0 700000 0 1 4 1 0 0xffffffff 0 0",
            "add port tm leaf node {} 1 700000 0 2 4 1 0 0xffffffff 0 0",
            "add port tm leaf node {} 2 700000 0 3 4 4 0 0xffffffff 0 0",
            "add port tm leaf node {} 3 700000 0 4 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 4 600000 0 1 4 4 0 0xffffffff 0 0",
            "add port tm leaf node {} 5 600000 0 2 4 3 0 0xffffffff 0 0",
            "add port tm leaf node {} 6 600000 0 3 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 7 600000 0 4 4 -1 0 0xffffffff 0 0",
            "port tm hierarchy commit {} no",
        ]
        for cmd in cmds:
            cmd = cmd.format(self.ice_25G_port_id)
            self.pmd_output.execute_cmd(cmd)
        self.pmd_output.execute_cmd("start")

        traffic_tasks = [
            [8.25, "Gbps", self.ice_25G_port_id],
        ]
        results = self.get_traffic_results()
        real_bps = self.check_traffic_throughput(traffic_tasks, results)
        expected = [[0, 0, 0, 0], [0, 0, 3, 4], [1, 1]]
        expected_queue = [
            [0, 10, "MBps"],
            [1, 10, "MBps"],
            [2, 40, "MBps"],
            [3, real_bps / 2 / 1e6 / 8 - 10 - 10 - 40, "MBps", "rest"],
            [4, 40, "MBps"],
            [5, 30, "MBps"],
            [6, (real_bps / 2 / 1e6 / 8 - 40 - 30) * 3 / 7, "MBps", "rest"],
            [7, (real_bps / 2 / 1e6 / 8 - 40 - 30) * 4 / 7, "MBps", "rest"],
        ]
        self.check_queue_throughout(results, expected_queue)
        self.check_queue_ratio(results, expected, check_group=True)

    def test_perf_negative_case(self):

        self.launch_testpmd(param="--rxq=16 --txq=16")
        cmd1 = [
            "add port tm node shaper profile {} 1 100000000 0 100000000 0 0 0",
            "add port tm nonleaf node {} 1000000 -1 0 1 0 -1 1 0 0",
            "add port tm nonleaf node {} 900000 1000000 0 1 1 -1 1 0 0",
            "add port tm nonleaf node {} 800000 900000 0 1 2 -1 1 0 0",
            "add port tm nonleaf node {} 700000 800000 0 1 3 -1 1 0 0",
            "add port tm nonleaf node {} 600000 800000 0 2 3 -1 1 0 0",
        ]
        output = ""
        for cmd in cmd1:
            cmd = cmd.format(self.ice_25G_port_id)
            output += self.pmd_output.execute_cmd(cmd)
        check_msg = "ice_tm_node_add(): weight != 1 not supported in level 3"
        self.verify(
            check_msg in output, "Configure invalid parameters, report expected errors."
        )
        cmd2 = [
            "port stop {}",
            "del port tm node {} 600000",
            "add port tm nonleaf node {} 600000 800000 0 1 3 -1 1 0 0",
            "port start {}",
            "add port tm leaf node {} 0 700000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 1 700000 0 2 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 2 700000 0 3 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 3 700000 0 201 4 -1 0 0xffffffff 0 0",
        ]
        output = ""
        for cmd in cmd2:
            cmd = cmd.format(self.ice_25G_port_id)
            output += self.pmd_output.execute_cmd(cmd)
        check_msg = "node weight: weight must be between 1 and 200 (error 21)"
        self.verify(
            check_msg in output, "Configure invalid parameters, report expected errors."
        )
        cmd3 = [
            "add port tm leaf node {} 3 700000 0 200 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 4 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 5 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 6 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 7 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 8 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 9 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 10 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 11 600000 8 1 4 -1 0 0xffffffff 0 0",
        ]
        output = ""
        for cmd in cmd3:
            cmd = cmd.format(self.ice_25G_port_id)
            output += self.pmd_output.execute_cmd(cmd)
        check_msg = "node priority: priority should be less than 8 (error 20)"
        self.verify(
            check_msg in output, "Configure invalid parameters, report expected errors."
        )
        cmd4 = [
            "add port tm leaf node {} 11 600000 7 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 12 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 13 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 14 600000 0 1 4 -1 0 0xffffffff 0 0",
            "add port tm leaf node {} 15 600000 0 1 4 -1 0 0xffffffff 0 0",
            "port tm hierarchy commit {} no",
        ]
        output = ""
        for cmd in cmd4:
            cmd = cmd.format(self.ice_25G_port_id)
            output += self.pmd_output.execute_cmd(cmd)
        check_msg = "ice_move_recfg_lan_txq(): move lan queue 12 failed\r\nice_hierarchy_commit(): move queue 12 failed\r\ncause unspecified: (no stated reason) (error 1)"
        self.verify(
            check_msg in output, "Configure invalid parameters, report expected errors."
        )

    def tear_down(self):
        """
        Run after each test case.
        """
        self.close_testpmd()
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
