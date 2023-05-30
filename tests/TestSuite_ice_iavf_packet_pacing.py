# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2022 Intel Corporation
#

import copy
import os
import re
import time
from pprint import pformat

from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase
from framework.utils import GREEN, RED


class TestICEIavfPacketPacing(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.verify(
            self.nic in ["ICE_25G-E810C_SFP", "ICE_100G-E810C_QSFP"],
            "%s nic not support vf timestamp" % self.nic,
        )
        self.dut_ports = self.dut.get_ports(self.nic)
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.tester_port0 = self.tester.get_local_port(self.dut_ports[0])
        self.tester_iface0 = self.tester.get_interface(self.tester_port0)
        self.pkt = Packet()
        self.pmdout = PmdOutput(self.dut)

        self.vf_driver = self.get_suite_cfg()["vf_driver"]
        if self.vf_driver is None:
            self.vf_driver = "vfio-pci"
        self.pf0_intf = self.dut.ports_info[self.dut_ports[0]]["intf"]

        # get dts output path
        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        else:
            cur_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            self.output_path = os.sep.join([cur_path, self.logger.log_path])
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.path = self.dut.apps_name["test-pmd"]

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def launch_testpmd(self, allowlist, line_option=""):
        """
        start testpmd
        """
        # Prepare testpmd EAL and parameters
        output = self.pmdout.start_testpmd(
            socket=self.ports_socket,
            prefix="tx",
            eal_param=allowlist,
            param=line_option,
        )
        # test link status
        res = self.pmdout.wait_link_status_up("all", timeout=15)
        self.verify(res is True, "there have port link is down")
        return output

    def close_testpmd(self):
        self.dut.send_expect("quit", "# ", 30)
        time.sleep(5)

    def create_vf(self, vf_num):
        self.dut.bind_interfaces_linux("ice")
        self.dut.generate_sriov_vfs_by_port(self.dut_ports[0], vf_num)
        self.sriov_vfs_port = self.dut.ports_info[self.dut_ports[0]]["vfs_port"]
        self.dut.send_expect("ifconfig %s up" % self.pf0_intf, "# ")
        if vf_num >= 2:
            self.dut.send_expect(
                "ip link set dev %s vf 0 trust on" % self.pf0_intf, "# "
            )
            self.dut.send_expect(
                "ip link set %s vf 1 mac 00:11:22:33:44:55" % self.pf0_intf, "#"
            )
            self.vf0_pci = self.sriov_vfs_port[0].pci
            self.vf1_pci = self.sriov_vfs_port[1].pci
        else:
            self.dut.send_expect(
                "ip link set %s vf 0 mac 00:11:22:33:44:55" % self.pf0_intf, "#"
            )
            self.vf0_pci = self.sriov_vfs_port[0].pci
        try:
            for port in self.sriov_vfs_port:
                port.bind_driver(self.vf_driver)
        except Exception as e:
            self.destroy_vf()
            raise Exception(e)

    def destroy_vf(self):
        self.dut.destroy_sriov_vfs_by_port(self.dut_ports[0])
        self.dut.send_expect("rmmod ice", "# ", 15)
        self.dut.send_expect("modprobe ice", "# ", 15)

    def testpmd_query_stats(self):
        output = self.dut.send_expect("show port stats all", "testpmd> ", 20)
        self.logger.info(output)
        if not output:
            return
        port_pat = ".*NIC statistics for (port \d+) .*"
        tx_pat = ".*Tx-pps:\s+(\d+)\s+Tx-bps:\s+(\d+).*"
        port = re.findall(port_pat, output, re.M)
        tx = re.findall(tx_pat, output, re.M)
        if not port or not tx:
            return
        stat = {}
        for port_id, (tx_pps, tx_bps) in zip(port, tx):
            stat[port_id] = {
                "tx_pps": float(tx_pps),
                "tx_bps": float(tx_bps),
            }
        self.pmd_stat = stat

    def get_queue_packets_stats(self, port):
        output = self.dut.send_expect("stop", "testpmd> ")
        self.logger.info(output)
        p = re.compile("TX Port= %d/Queue=.*\n.*TX-packets: ([0-9]+)\s" % port)
        queue_pkts = p.findall(output)
        queue_pkts = list(map(int, queue_pkts))
        if not queue_pkts:
            return {}
        return queue_pkts

    def is_expected_throughput(self, expected, pmd_stat):
        _expected, unit, port = expected
        port = port
        real_stat = pmd_stat.get(f"port {port}", {})
        key = "tx_bps"
        real_bps = real_stat.get(key) or 0
        if real_bps == 0 and _expected == 0:
            return True
        if not _expected:
            return False
        bias = 10
        if unit == "MBps":
            _bias = 100 * abs((real_bps / 8 / 1e6 - _expected) / _expected)
            return _bias < bias
        return True

    def set_fields(self):
        fields_config = {
            "ip": {
                "src": {
                    "start": "198.18.0.0",
                    "end": "198.18.0.255",
                    "step": 1,
                    "action": "random",
                },
            },
        }
        return fields_config

    def check_traffic(self, expected, frame_size=64):
        # create pcap file
        dmac = "00:11:22:33:44:55"
        payload_size = frame_size - HEADER_SIZE["ip"] - HEADER_SIZE["eth"]
        pcap = os.sep.join([self.output_path, "dts0.pcap"])
        self.tester.scapy_append(
            'wrpcap("%s", [Ether(dst="%s")/IP(src="198.18.0.0",dst="198.28.0.0")/("X"*%d)])'
            % (pcap, dmac, payload_size)
        )
        self.tester.scapy_execute()
        tgen_input = []
        tgen_input.append(
            (
                self.tester.get_local_port(self.dut_ports[0]),
                self.tester.get_local_port(self.dut_ports[0]),
                "%s" % pcap,
            )
        )

        # clear streams before add new streams
        vm_config = self.set_fields()
        self.tester.pktgen.clear_streams()

        streams = self.pktgen_helper.prepare_stream_from_tginput(
            tgen_input, 100, vm_config, self.tester.pktgen
        )
        traffic_opt = {
            "method": "throughput",
            "duration": 20,
            "interval": 15,
            "callback": self.testpmd_query_stats,
        }
        results = []
        result = self.tester.pktgen.measure_throughput(
            stream_ids=[0], options=traffic_opt
        )

        pmd_stat = self.pmd_stat
        status = self.is_expected_throughput(expected, pmd_stat)
        msg = (
            f"{pformat(expected)}"
            " not get expected throughput value, real is: "
            f"{pformat(pmd_stat)}"
        )
        self.verify(status, msg)

        _, _, port = expected
        queue_pkts = self.get_queue_packets_stats(port)
        results.append([result, pmd_stat, queue_pkts])
        return results

    def check_queue_pkts_ratio(self, expected, result):
        total_pkts = sum(result)
        total_ratio = sum(expected)
        ratio = []
        for idx, result in enumerate(result):
            percentage = 100 * result / total_pkts
            ratio.append(percentage)
        bias = 10
        for idx, percentage in enumerate(expected):
            percentage = 100 * percentage / total_ratio
            _bias = 100 * abs(ratio[idx] - percentage) / percentage
            self.logger.info((ratio[idx], percentage))
            if _bias < bias:
                continue
            else:
                msg = "can not get expected queue ratio"
                self.verify(False, msg)

    def check_output(self, expected, output):
        if isinstance(expected, str):
            expected = [expected]
        for _expected in expected:
            self.verify(
                _expected in output, f"expected <{_expected}> message not display"
            )

    def verify_without_quanta_size_check_peak_tb_rate(self):
        allowlist = f"-a {self.vf0_pci}"
        line_option = ""
        self.launch_testpmd(allowlist, line_option)
        self.dut.send_expect("port stop all", "testpmd> ")
        self.dut.send_expect(
            "add port tm node shaper profile 0 1 1000000 0 612980769 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect("port tm hierarchy commit 0 no", "testpmd> ")
        self.dut.send_expect("port start all", "testpmd> ")
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        expected_throughput = (612, "MBps", 0)

        results = self.check_traffic(expected_throughput)

    def verify_single_queue_check_peak_tb_rate(self):
        allowlist = f"-a {self.vf0_pci},quanta_size=1024"
        line_option = ""
        self.launch_testpmd(allowlist, line_option)
        self.dut.send_expect("port stop all", "testpmd> ")
        self.dut.send_expect(
            "add port tm node shaper profile 0 1 1000000 0 612980769 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect("port tm hierarchy commit 0 no", "testpmd> ")
        self.dut.send_expect("port start all", "testpmd> ")
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        expected_throughput = (612, "MBps", 0)

        results = self.check_traffic(expected_throughput)

    def verify_multi_queues_check_peak_tb_rate(self):
        allowlist = f"-a {self.vf0_pci},quanta_size=1024"
        line_option = "--rxq=8 --txq=8"
        self.launch_testpmd(allowlist, line_option)
        self.dut.send_expect("port stop all", "testpmd> ")
        self.dut.send_expect(
            "add port tm node shaper profile 0 1 1000000 0 100000000 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 2 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 3 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 4 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 5 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 6 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 7 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect("port tm hierarchy commit 0 no", "testpmd> ")
        self.dut.send_expect("port start all", "testpmd> ")
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        expected_throughput = (800, "MBps", 0)
        expected_ratio = [1, 1, 1, 1, 1, 1, 1, 1]

        results = self.check_traffic(expected_throughput)
        self.check_queue_pkts_ratio(expected_ratio, results[-1][-1])

    def verify_modify_quanta_size_check_peak_tb_rate(self):
        allowlist = f"-a {self.vf0_pci},quanta_size=4096"
        line_option = "--rxq=8 --txq=8"
        self.launch_testpmd(allowlist, line_option)
        self.dut.send_expect("port stop all", "testpmd> ")
        self.dut.send_expect(
            "add port tm node shaper profile 0 1 1000000 0 100000000 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 2 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 3 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 4 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 5 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 6 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 7 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect("port tm hierarchy commit 0 no", "testpmd> ")
        self.dut.send_expect("port start all", "testpmd> ")
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        expected_throughput = (800, "MBps", 0)
        expected_ratio = [1, 1, 1, 1, 1, 1, 1, 1]

        results = self.check_traffic(expected_throughput)
        self.check_queue_pkts_ratio(expected_ratio, results[-1][-1])

    def verify_multi_queues_with_diff_rate_limit_check_peak_tb_rate(self):
        allowlist = f"-a {self.vf0_pci},quanta_size=1024"
        line_option = "--rxq=8 --txq=8"
        self.launch_testpmd(allowlist, line_option)
        self.dut.send_expect("port stop all", "testpmd> ")
        self.dut.send_expect(
            "add port tm node shaper profile 0 1 1000000 0 10000000 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm node shaper profile 0 2 1000000 0 20000000 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm node shaper profile 0 3 1000000 0 30000000 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm node shaper profile 0 4 1000000 0 40000000 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm node shaper profile 0 5 1000000 0 50000000 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm node shaper profile 0 6 1000000 0 60000000 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm node shaper profile 0 7 1000000 0 70000000 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm node shaper profile 0 8 1000000 0 80000000 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 1 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 2 900 0 1 2 3 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 3 900 0 1 2 4 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 4 900 0 1 2 5 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 5 900 0 1 2 6 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 6 900 0 1 2 7 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 7 900 0 1 2 8 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect("port tm hierarchy commit 0 no", "testpmd> ")
        self.dut.send_expect("port start all", "testpmd> ")
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        expected_throughput = (360, "MBps", 0)
        expected_ratio = [1, 2, 3, 4, 5, 6, 7, 8]

        results = self.check_traffic(expected_throughput)
        self.check_queue_pkts_ratio(expected_ratio, results[-1][-1])

    def verify_port_rate_limit_less_than_queue_rate_limit(self):
        allowlist = f"-a {self.vf0_pci},cap=dcf -a {self.vf1_pci},quanta_size=1024"
        line_option = "--rxq=8 --txq=8 --port-topology=loop"
        self.launch_testpmd(allowlist, line_option)
        self.dut.send_expect("port stop all", "testpmd> ")
        self.dut.send_expect(
            "add port tm node shaper profile 0 1 1000000 0 100000000 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm node shaper profile 1 2 1000000 0 612980769 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 1 1000 -1 0 1 0 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 1 900 1000 0 1 1 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 0 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 1 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 2 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 3 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 4 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 5 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 6 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 7 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect("port tm hierarchy commit 0 no", "testpmd> ")
        self.dut.send_expect("port tm hierarchy commit 1 no", "testpmd> ")
        self.dut.send_expect("port start all", "testpmd> ")
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        expected_throughput = (100, "MBps", 1)
        expected_ratio = [1, 1, 1, 1, 1, 1, 1, 1]

        results = self.check_traffic(expected_throughput)
        self.check_queue_pkts_ratio(expected_ratio, results[-1][-1])

    def verify_port_rate_limit_more_than_queue_rate_limit(self):
        allowlist = f"-a {self.vf0_pci},cap=dcf -a {self.vf1_pci},quanta_size=1024"
        line_option = "--rxq=8 --txq=8 --port-topology=loop"
        self.launch_testpmd(allowlist, line_option)
        self.dut.send_expect("port stop all", "testpmd> ")
        self.dut.send_expect(
            "add port tm node shaper profile 0 1 1000000 0 200000000 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm node shaper profile 1 2 1000000 0 10000000 0 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 1 1000 -1 0 1 0 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm nonleaf node 1 900 1000 0 1 1 -1 1 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 0 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 1 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 2 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 3 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 4 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 5 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 6 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect(
            "add port tm leaf node 1 7 900 0 1 2 2 0 0xffffffff 0 0", "testpmd> "
        )
        self.dut.send_expect("port tm hierarchy commit 0 no", "testpmd> ")
        self.dut.send_expect("port tm hierarchy commit 1 no", "testpmd> ")
        self.dut.send_expect("port start all", "testpmd> ")
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        expected_throughput = (80, "MBps", 1)
        expected_ratio = [1, 1, 1, 1, 1, 1, 1, 1]

        results = self.check_traffic(expected_throughput)
        self.check_queue_pkts_ratio(expected_ratio, results[-1][-1])

    def test_perf_without_quanta_size_check_peak_tb_rate(self):
        self.create_vf(vf_num=1)
        self.verify_without_quanta_size_check_peak_tb_rate()

    def test_perf_single_queue_check_peak_tb_rate(self):
        self.create_vf(vf_num=1)
        self.verify_single_queue_check_peak_tb_rate()

    def test_perf_multi_queues_check_peak_tb_rate(self):
        self.create_vf(vf_num=1)
        self.verify_multi_queues_check_peak_tb_rate()

    def test_perf_modify_quanta_size_check_peak_tb_rate(self):
        self.create_vf(vf_num=1)
        self.verify_modify_quanta_size_check_peak_tb_rate()

    def test_perf_invalid_quanta_size_check_peak_tb_rate(self):
        self.create_vf(vf_num=1)
        output = self.launch_testpmd(
            allowlist=f"-a {self.vf0_pci},quanta_size=1000", line_option=""
        )
        expected = "iavf_parse_devargs(): invalid quanta size"
        self.check_output(expected, output)

    def test_perf_multi_queues_with_diff_rate_limit_check_peak_tb_rate(self):
        self.create_vf(vf_num=1)
        self.verify_multi_queues_with_diff_rate_limit_check_peak_tb_rate()

    def test_perf_port_rate_limit_less_than_queue_rate_limit(self):
        self.create_vf(vf_num=2)
        self.verify_port_rate_limit_less_than_queue_rate_limit()

    def test_perf_port_rate_limit_more_than_queue_rate_limit(self):
        self.create_vf(vf_num=2)
        self.verify_port_rate_limit_more_than_queue_rate_limit()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.close_testpmd()
        self.destroy_vf()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
