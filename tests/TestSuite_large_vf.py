# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
#

import re
import time

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.utils import GREEN, RED

multi_fdir_queue_group = {
    "match": [
        "Ether(dst='00:11:22:33:44:55')/IP(src=RandIP(),dst='192.168.0.21')/UDP(sport=22,dport=23)/Raw('x'*80)",
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='2001::2')/UDP(sport=RandShort())/('x'*80)",
        "Ether(dst='00:11:22:33:44:55')/IP()/TCP(sport=22, dport=RandShort())/Raw('x'*80)",
        "Ether(dst='00:11:22:33:44:55')/IPv6(dst='2001::2')/TCP(dport=23, sport=RandShort())/Raw('x'*80)",
    ],
    "mismatch": [
        "Ether(dst='00:11:22:33:44:55')/IP(src=RandIP(),dst='192.168.0.22')/UDP(sport=22,dport=24)/Raw('x'*80)",
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='2001::3')/UDP(sport=RandShort())/('x'*80)",
        "Ether(dst='00:11:22:33:44:55')/IP()/TCP(sport=23, dport=RandShort())/Raw('x'*80)",
        "Ether(dst='00:11:22:33:44:55')/IPv6(dst='2001::2')/TCP(dport=22, sport=RandShort())/Raw('x'*80)",
    ],
}

check_multi_fdir_consistent_queue_group = {
    "match": [
        {"matched_id": "0x1", "queue": (0, 63)},
        {"matched_id": "0x2", "queue": (64, 127)},
        {"matched_id": "0x3", "queue": (128, 191)},
        {"matched_id": "0x4", "queue": (192, 255)},
    ],
    "mismatch": {"queue": (0, 63)},
}

check_multi_fdir_inconsistent_queue_group = {
    "match": [
        {"matched_id": "0x1", "queue": (5, 20)},
        {"matched_id": "0x2", "queue": (80, 87)},
        {"matched_id": "0x3", "queue": (150, 213)},
        {"matched_id": "0x4", "queue": (252, 255)},
    ],
    "mismatch": {"queue": (0, 63)},
}

multi_fdir_consistent_queue_group = {
    "name": "test_multi_fdir_consistent_queue_group",
    "param": "--txq=256 --rxq=256",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 / end actions rss queues 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 end / mark id 1 / end",
        "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / end actions rss queues 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 end / mark id 2 / end",
        "flow create 0 ingress pattern eth / ipv4 / tcp src is 22 / end actions rss queues 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 end / mark id 3 / end",
        "flow create 0 ingress pattern eth / ipv6 dst is 2001::2 / tcp dst is 23 / end actions rss queues 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207 208 209 210 211 212 213 214 215 216 217 218 219 220 221 222 223 224 225 226 227 228 229 230 231 232 233 234 235 236 237 238 239 240 241 242 243 244 245 246 247 248 249 250 251 252 253 254 255 end / mark id 4 / end",
    ],
    "scapy_str": multi_fdir_queue_group,
    "check_param": check_multi_fdir_consistent_queue_group,
    "count": 1000,
}

multi_fdir_inconsistent_queue_group = {
    "name": "test_multi_fdir_inconsistent_queue_group",
    "param": "--txq=256 --rxq=256",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 / end actions rss queues 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 end / mark id 1 / end",
        "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / end actions rss queues 80 81 82 83 84 85 86 87 end / mark id 2 / end",
        "flow create 0 ingress pattern eth / ipv4 / tcp src is 22 / end actions rss queues 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207 208 209 210 211 212 213 end / mark id 3 / end",
        "flow create 0 ingress pattern eth / ipv6 dst is 2001::2 / tcp dst is 23 / end actions rss queues 252 253 254 255 end / mark id 4 / end",
    ],
    "scapy_str": multi_fdir_queue_group,
    "check_param": check_multi_fdir_inconsistent_queue_group,
    "count": 1000,
}

basic_rxtx = {
    "name": "test_basic_rxtx",
    "param": "--txq=256 --rxq=256",
    "scapy_str": "Ether(dst='00:11:22:33:44:55')/IP(src=RandIP(),dst='192.168.0.21')/UDP(sport=22,dport=23)/Raw('x'*80)",
    "check_param": [255, 63],
    "count": 1000,
}

different_queues_switch = {
    "name": "test_different_queues_switch",
    "q_num": [16, 256],
    "rule": [
        "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / end actions rss queues 1 2 3 4 end / mark id 1 / end",
        "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 / end actions rss queues 8 9 10 11 12 13 14 15 end / mark id 2 / end",
    ],
    "scapy_str": {
        "match": [
            "Ether(dst='00:11:22:33:44:55')/IPv6(src='2001::2')/UDP(sport=RandShort())/('x'*80)",
            "Ether(dst='00:11:22:33:44:55')/IP(src=RandIP(),dst='192.168.0.21')/UDP(sport=22,dport=23)/Raw('x'*80)",
        ],
        "mismatch": [
            "Ether(dst='00:11:22:33:44:55')/IPv6(src='2001::3')/UDP(sport=RandShort())/('x'*80)",
            "Ether(dst='00:11:22:33:44:55')/IP(src=RandIP(),dst='192.168.0.22')/UDP(sport=22,dport=24)/Raw('x'*80)",
        ],
    },
    "check_param": {
        "match": [
            {"matched_id": "0x1", "queue": (1, 4)},
            {"matched_id": "0x2", "queue": (8, 15)},
        ],
        "mismatch": {"queue": (0, 15)},
    },
    "count": 1000,
}

pf_large_vf_fdir_coexist = {
    "name": "test_pf_large_vf_fdir_coexist",
    "param": [21, 63],
    "check_param": (54, 63),
    "count": 1,
}

exceed_256_queues = {
    "name": "test_exceed_256_queues",
    "param": ["--txq=512 --rxq=512", "--txq=256 --rxq=256"],
    "check_param": "Fail: input txq (512) can't be greater than max_tx_queues (256)",
}

more_than_3_vfs_256_queues = {
    "name": "test_more_than_3_vfs_256_queues",
    "param": "--txq=256 --rxq=256",
    "check_param": "Cause: Start ports failed",
}

max_vfs_256_queues_3 = [
    multi_fdir_consistent_queue_group,
    multi_fdir_inconsistent_queue_group,
    basic_rxtx,
    different_queues_switch,
    pf_large_vf_fdir_coexist,
    exceed_256_queues,
    more_than_3_vfs_256_queues,
]

multi_fdir_among = {
    "name": "test_multi_fdir_among",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 / end actions rss queues 0 1 end / mark id 1 / end",
        "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / end actions rss queues 2 3 end / mark id 2 / end",
    ],
    "scapy_str": {
        "match": [
            "Ether(dst='00:11:22:33:44:55')/IP(src=RandIP(),dst='192.168.0.21')/UDP(sport=22,dport=23)/Raw('x'*80)",
            "Ether(dst='00:11:22:33:44:55')/IPv6(src='2001::2')/UDP(sport=RandShort())/('x'*80)",
        ],
        "mismatch": [
            "Ether(dst='00:11:22:33:44:55')/IP(src=RandIP(),dst='192.168.0.22')/UDP(sport=22,dport=24)/Raw('x'*80)",
            "Ether(dst='00:11:22:33:44:55')/IPv6(src='2001::3')/UDP(sport=RandShort())/('x'*80)",
        ],
    },
    "check_param": {
        "match": [
            {"matched_id": "0x1", "queue": (0, 1)},
            {"matched_id": "0x2", "queue": (2, 3)},
        ],
        "mismatch": {"queue": (0, 3)},
    },
    "count": 1000,
}

more_than_4_queues_max_vfs = {
    "name": "test_more_than_4_queues_max_vfs",
    "param": ["--txq=4 --rxq=4"],
    "check_param": "request queues from PF failed",
}

more_than_max_vfs_4_queues = {
    "name": "test_more_than_max_vfs_4_queues",
    "check_param": "-bash: echo: write error: Numerical result out of range",
}

max_vfs_4_queues = [
    multi_fdir_among,
    more_than_4_queues_max_vfs,
    more_than_max_vfs_4_queues,
]


class TestLargeVf(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(
            self.nic in ["ICE_25G-E810C_SFP", "ICE_100G-E810C_QSFP"],
            "%s nic not support large vf" % self.nic,
        )
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.vf_mac = "00:11:22:33:44:55"
        self.tester_port0 = self.tester.get_local_port(self.dut_ports[0])
        self.tester_iface0 = self.tester.get_interface(self.tester_port0)
        self.used_dut_port = self.dut_ports[0]
        self.pf0_intf = self.dut.ports_info[self.dut_ports[0]]["intf"]
        self.pf0_pci = self.dut.ports_info[self.dut_ports[0]]["pci"]
        self.max_vf_num = int(
            self.dut.send_expect(
                "cat /sys/bus/pci/devices/%s/sriov_totalvfs" % self.pf0_pci, "#"
            )
        )
        self.pf0_mac = self.dut.get_mac_address(0)

        self.vf_flag = False
        # set vf driver
        self.vf_driver = "vfio-pci"
        self.dut.send_expect("modprobe vfio-pci", "#")

        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)

        self.app_path = self.dut.apps_name["test-pmd"]
        self.vf_num = 7 if self.max_vf_num > 128 else 3
        self.pmdout_list = []
        self.session_list = []
        for i in range(self.vf_num):
            session = self.dut.new_session()
            self.session_list.append(session)
            pmdout = PmdOutput(self.dut, session)
            self.pmdout_list.append(pmdout)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def create_iavf(self, vf_numbers):
        # Generate 3 VFs on each PF and set mac address for VF0
        self.dut.bind_interfaces_linux("ice")
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port, vf_numbers)
        self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]["vfs_port"]
        self.vf_flag = True

        try:
            for port in self.sriov_vfs_port:
                port.bind_driver(self.drivername)
            self.vf0_prop = {"opt_host": self.sriov_vfs_port[0].pci}
            self.dut.send_expect("ifconfig %s up" % self.pf0_intf, "# ")
            self.dut.send_expect(
                "ip link set %s vf 0 mac %s" % (self.pf0_intf, self.vf_mac), "# "
            )
        except Exception as e:
            self.destroy_iavf()
            raise Exception(e)

    def destroy_iavf(self):
        if self.vf_flag is True:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.vf_flag = False

    def launch_testpmd(self, param, total=False, retry_times=3):
        if total:
            param = param + " --total-num-mbufs=500000"
        while retry_times:
            try:
                self.pmd_output.start_testpmd(
                    "all",
                    param=param,
                    ports=[self.sriov_vfs_port[0].pci],
                    socket=self.ports_socket,
                )
                break
            except Exception as e:
                self.logger.info("start testpmd occurred exception: {}".format(e))
            retry_times = retry_times - 1
            time.sleep(1)
            self.logger.info("try start testpmd the {} times".format(retry_times))

    def config_testpmd(self):
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("port config all rss all")
        self.pmd_output.execute_cmd("start")

    def send_packets(self, packets, count):
        self.pkt.update_pkt(packets)
        self.pkt.send_pkt(crb=self.tester, tx_port=self.tester_iface0, count=count)

    def send_pkts_getouput(self, pkts, count):
        self.send_packets(pkts, count)
        time.sleep(1)
        out_info = self.dut.get_session_output(timeout=1)
        out_pkt = self.pmd_output.execute_cmd("stop")
        time.sleep(1)
        out = out_info + out_pkt
        self.pmd_output.execute_cmd("start")
        self.pmd_output.execute_cmd("clear port stats all")
        return out

    def rte_flow_process(self, vectors):
        test_results = {}
        for tv in vectors:
            try:
                subcase_name = tv["name"]
                self.logger.info("============subcase %s============" % subcase_name)
                if subcase_name == "test_basic_rxtx":
                    self.pmd_output.execute_cmd("flow flush 0")
                    self.check_txonly_pkts()
                    self.pmd_output.execute_cmd("set fwd rxonly")
                    out = self.send_pkts_getouput(tv["scapy_str"], tv["count"])
                    self.check_iavf_fdir_value(out, tv["check_param"][1], tv["count"])
                elif subcase_name == "test_different_queues_switch":
                    for i in range(2):
                        # set rxq txq of 16
                        self.check_rxqtxq_number(tv["q_num"][0])
                        self.create_fdir_rule(tv["rule"])
                        self.check_match_mismatch_pkts(tv)
                        # set rxq txq of 16
                        self.check_rxqtxq_number(tv["q_num"][1])
                        self.create_fdir_rule(vectors[0]["rule"])
                        self.check_match_mismatch_pkts(vectors[0])
                elif subcase_name == "test_pf_large_vf_fdir_coexist":
                    self.destroy_pf_rule(self.pmdout_list[0], self.pf0_intf)
                    self.create_pf_rule(
                        self.pmdout_list[0],
                        self.pf0_intf,
                        tv["param"][0],
                        tv["param"][1],
                    )
                    self.send_pkts_pf_check(
                        self.pmdout_list[0],
                        self.pf0_intf,
                        self.pf0_mac,
                        tv["param"][0],
                        tv["check_param"],
                        tv["count"],
                    )
                    self.create_fdir_rule(vectors[0]["rule"])
                    self.check_match_mismatch_pkts(vectors[0])
                    self.destroy_pf_rule(self.pmdout_list[0], self.pf0_intf)
                elif subcase_name == "test_exceed_256_queues":
                    self.pmd_output.execute_cmd("quit", "#")
                    eal_param = self.dut.create_eal_parameters(
                        prefix="port0vf0", ports=[self.sriov_vfs_port[0].pci]
                    )
                    cmd = (
                        "{} ".format(self.app_path)
                        + eal_param
                        + "-- -i "
                        + tv["param"][0]
                    )
                    out = self.pmd_output.execute_cmd(cmd, "# ")
                    self.verify(
                        tv["check_param"] in out, "fail: testpmd start successfully"
                    )
                    self.launch_testpmd(tv["param"][1])
                    self.check_rxqtxq_number(512, tv["check_param"])
                elif subcase_name == "test_more_than_3_vfs_256_queues":
                    self.pmd_output.execute_cmd("quit", "#")
                    # start testpmd use 256 queues
                    for i in range(self.vf_num + 1):
                        if self.max_vf_num == 64:
                            self.pmdout_list[0].start_testpmd(
                                param=tv["param"],
                                ports=[self.sriov_vfs_port[0].pci],
                                prefix="port0vf0",
                            )
                            eal_param = self.dut.create_eal_parameters(
                                fixed_prefix=True, ports=[self.sriov_vfs_port[1].pci]
                            )
                            cmd = (
                                "{} ".format(self.app_path)
                                + eal_param
                                + "-- -i "
                                + tv["param"]
                            )
                            out = self.pmd_output.execute_cmd(cmd, "#")
                            self.verify(
                                tv["check_param"] in out,
                                "fail: testpmd start successfully",
                            )
                            self.pmdout_list[0].execute_cmd("quit", "# ")
                            break
                        else:
                            if i < self.vf_num:
                                self.pmdout_list[i].start_testpmd(
                                    param=tv["param"],
                                    ports=[self.sriov_vfs_port[i].pci],
                                    prefix="port0vf{}".format(i),
                                )
                            else:
                                # start fourth testpmd failed
                                eal_param = self.dut.create_eal_parameters(
                                    fixed_prefix=True,
                                    ports=[self.sriov_vfs_port[-1].pci],
                                )
                                cmd = (
                                    "{} ".format(self.app_path)
                                    + eal_param
                                    + "-- -i "
                                    + tv["param"]
                                )
                                out = self.pmd_output.execute_cmd(cmd, "#")
                                self.verify(
                                    tv["check_param"] in out,
                                    "fail: testpmd start successfully",
                                )
                                # quit all testpmd
                                self.pmdout_list[0].execute_cmd("quit", "# ")
                                self.pmdout_list[1].execute_cmd("quit", "# ")
                                self.pmdout_list[2].execute_cmd("quit", "# ")
                                if self.vf_num > 3:
                                    self.pmdout_list[3].execute_cmd("quit", "# ")
                                    self.pmdout_list[4].execute_cmd("quit", "# ")
                                    self.pmdout_list[5].execute_cmd("quit", "# ")
                                    self.pmdout_list[6].execute_cmd("quit", "# ")

                # case 2: max_vfs_4_queues
                elif subcase_name == "test_multi_fdir_among":
                    self.create_fdir_rule(tv["rule"])
                    self.check_match_mismatch_pkts(tv)
                elif subcase_name == "test_more_than_max_vfs_4_queues":
                    self.pmd_output.execute_cmd("quit", "#")
                    out = self.dut.send_expect(
                        "echo {} > /sys/bus/pci/devices/{}/sriov_numvfs".format(
                            self.max_vf_num, self.pf0_pci
                        ),
                        "# ",
                    )
                    self.verify(tv["check_param"] not in out, "fail: create vfs failed")
                    out = self.dut.send_expect(
                        "echo {} > /sys/bus/pci/devices/{}/sriov_numvfs".format(
                            self.max_vf_num + 1, self.pf0_pci
                        ),
                        "# ",
                    )
                    self.verify(
                        tv["check_param"] in out, "fail: create vfs successfully"
                    )
                elif subcase_name == "test_more_than_4_queues_max_vfs":
                    self.pmd_output.execute_cmd("quit", "# ")
                    pmd_number = 4 if self.max_vf_num > 64 else 2
                    eal_param = ""
                    for port in range(self.max_vf_num):
                        eal_param += "-a %s " % self.sriov_vfs_port[port].pci
                    for i in range(pmd_number):
                        self.pmdout_list[i].start_testpmd(
                            "all",
                            eal_param=eal_param,
                            param=tv["param"][0],
                            prefix="pmd{}".format(i),
                        )
                    for j in range(pmd_number):
                        if j == pmd_number - 1:
                            self.pmdout_list[j].execute_cmd("stop")
                            self.pmdout_list[j].execute_cmd("port stop all")
                            self.pmdout_list[j].execute_cmd("port config all rxq 8")
                            out = self.pmdout_list[j].execute_cmd("port start all")
                            self.verify(
                                tv["check_param"] in out,
                                "fail: testpmd start successfully",
                            )
                        else:
                            self.pmdout_list[j].execute_cmd("stop")
                            self.pmdout_list[j].execute_cmd("port stop all")
                            self.pmdout_list[j].execute_cmd("port config all rxq 8")
                            self.pmdout_list[j].execute_cmd("port start all")
                    # quit all testpmd
                    for k in range(pmd_number):
                        self.pmdout_list[k].execute_cmd("quit", "# ")
                else:
                    self.create_fdir_rule(tv["rule"])
                    self.check_match_mismatch_pkts(tv)
                test_results[tv["name"]] = True
                print((GREEN("====case passed: %s====" % tv["name"])))
            except Exception as e:
                print((RED(e)))
                test_results[tv["name"]] = False
                print((GREEN("====case failed: %s====" % tv["name"])))
                continue
        failed_cases = []
        for k, v in list(test_results.items()):
            if not v:
                failed_cases.append(k)
        self.verify(all(test_results.values()), "{} failed.".format(failed_cases))

    def create_fdir_rule(self, rule):
        p = re.compile(r"Flow rule #(\d+) created")
        rule_list = []
        self.pmd_output.execute_cmd("flow flush 0")
        if isinstance(rule, list):
            for i in rule:
                out = self.pmd_output.execute_cmd(i)
                m = p.search(out)
                if m:
                    rule_list.append(m.group(1))
                else:
                    rule_list.append(False)
        elif isinstance(rule, str):
            out = self.pmd_output.execute_cmd(rule)
            m = p.search(out)
            if m:
                rule_list.append(m.group(1))
            else:
                rule_list.append(False)
        else:
            raise Exception("unsupported rule type, only accept list or str")
        self.verify(all(rule_list), "some rules create failed, result %s" % rule_list)

    def create_pf_rule(self, pmdout, pf_intf, ip, action):
        # count: create rules number
        queue_list = []
        for x in range(10):
            queue_list.append(action)
            cmd = "ethtool -N {} flow-type udp4 dst-ip 192.168.0.{} src-port 22 action {}".format(
                pf_intf, ip, action
            )
            pmdout.execute_cmd(cmd, "#")
            ip += 1
            action -= 1
        self.validation_pf_rule(pmdout, pf_intf, 10)

    def validation_pf_rule(self, pmdout, pf_intf, count=0):
        rule_str = "Total (\d+) rules"
        out = pmdout.execute_cmd("ethtool -n %s" % pf_intf, "#")
        rule_num = re.search(rule_str, out).group(1)
        self.verify(int(rule_num) == count, "Incorrect number of PF rules")

    def send_pkts_pf_check(self, pmdout, pf_intf, pf_mac, ip, check_param, count):
        for x in range(10):
            packet = "Ether(dst='{}')/IP(src=RandIP(),dst='192.168.0.{}')/UDP(sport=22,dport=23)/Raw('x'*80)".format(
                pf_mac, ip
            )
            self.send_packets(packet, 1)
            ip += 1
        time.sleep(1)
        out = pmdout.execute_cmd("ethtool -S %s" % pf_intf, "# ")
        for queue in range(check_param[0], check_param[1] + 1):
            packet_str = "rx_queue_%d_packets: (\d+)" % queue
            packet = re.search(packet_str, out).group(1)
            self.verify(
                int(packet) == count,
                "fail: queues %d received packets not matched" % queue,
            )

    def destroy_pf_rule(self, pmdout, pf_intf):
        rule_str = "Filter:.*?(\d+)"
        out = pmdout.execute_cmd("ethtool -n %s" % pf_intf, "#")
        rule_list = re.findall(rule_str, out)
        if rule_list:
            for rule in rule_list:
                cmd = "ethtool -N {} delete {}".format(pf_intf, rule)
                pmdout.execute_cmd(cmd, "#")
            self.validation_pf_rule(pmdout, pf_intf)

    def check_iavf_fdir_value(self, out, check_paeam, count, stats=False):
        """
        check match ID and rx/tx queue, pkts count
        """
        matched_str = "matched ID=(0x\d+)"
        queue_str = "RX Port=.*?Queue=.*?(\d+)"
        pkts_str = "Forward statistics for port.*?\n.*?RX-packets:\s(\d+)"
        match_list = re.findall(matched_str, out)
        if stats:
            self.verify(len(match_list) == 0, "fail: received packets have fdir ID")
        queue_list = re.findall(queue_str, out)
        pkts_num = re.search(pkts_str, out).group(1)
        # check pkts numbers
        self.verify(int(pkts_num) == count, "fail: received packets not matched")
        if isinstance(check_paeam, dict):
            # check matched
            if not stats:
                matched_id = check_paeam["matched_id"]
                self.verify(matched_id in match_list, "fail: matched id mismatch")
                matched_count = match_list.count(matched_id)
                self.verify(
                    len(match_list) == count == matched_count,
                    "fail: received packets by matched ID %s not matched"
                    % check_paeam["matched_id"],
                )
            # check queue id
            queue_id = check_paeam["queue"]
            self.verify(
                len(queue_list) == queue_id[1] - queue_id[0] + 1,
                "fail: received packets queues number not matched",
            )
            for q_id in range(queue_id[0], queue_id[1] + 1):
                self.verify(str(q_id) in queue_list, "fail: queue id not matched")
        else:
            self.verify(
                check_paeam + 1 == len(queue_list),
                "fail: received packets queues number not matched",
            )
            for q_id in range(check_paeam + 1):
                self.verify(str(q_id) in queue_list, "fail: queue id not matched")

    def check_match_mismatch_pkts(self, param):
        match_pkt = param["scapy_str"].get("match")
        mismatch_pkt = param["scapy_str"].get("mismatch")
        check_match_param = param["check_param"].get("match")
        check_mismatch_param = param["check_param"].get("mismatch")
        for pkt in match_pkt:
            out = self.send_pkts_getouput(pkt, param["count"])
            param_index = match_pkt.index(pkt)
            self.check_iavf_fdir_value(
                out, check_match_param[param_index], param["count"]
            )
        for pkt in mismatch_pkt:
            out = self.send_pkts_getouput(pkt, param["count"])
            self.check_iavf_fdir_value(
                out, check_mismatch_param, param["count"], stats=True
            )

    def check_txonly_pkts(self, q_num=256):
        queue_str = "RX Port=.*?Queue=.*?(\d+)"
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("set fwd txonly")
        self.pmd_output.execute_cmd("start")
        time.sleep(5)
        out = self.pmd_output.execute_cmd("stop")
        queue_list = re.findall(queue_str, out)
        self.verify(len(queue_list) == q_num, "fail: have queue not forwarded packet")
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("start")
        self.pmd_output.execute_cmd("clear port stats all")

    def check_rxqtxq_number(self, rxtx_num, check_param=None):
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("port stop all")
        self.pmd_output.execute_cmd("port config all rxq %s" % rxtx_num)
        if rxtx_num > 8:
            out = self.pmd_output.execute_cmd("port config all txq %s" % rxtx_num)
        else:
            out = self.pmd_output.execute_cmd("port start all")
        if check_param:
            self.verify(check_param in out, "fail: config port txq successfully")
        else:
            self.pmd_output.execute_cmd("port start all")
            self.pmd_output.execute_cmd("start")
            rxq_str = "Current number of RX queues: (\d+)"
            txq_str = "Current number of TX queues: (\d+)"
            out = self.pmd_output.execute_cmd("show port info all")
            rxq_num = re.search(rxq_str, out).group(1)
            txq_num = re.search(txq_str, out).group(1)
            self.verify(
                int(rxq_num) == int(txq_num) == rxtx_num,
                "current number of TX/RX queues not match",
            )
            self.check_txonly_pkts(rxtx_num)

    def test_3_vfs_256_queues(self):
        self.create_iavf(self.vf_num + 1)
        self.launch_testpmd("--rxq=256 --txq=256", total=True)
        self.config_testpmd()
        self.rte_flow_process(max_vfs_256_queues_3)

    def test_max_vfs_4_queues(self):
        session_last = self.dut.new_session()
        pmdout = PmdOutput(self.dut, session_last)
        self.pmdout_list.append(pmdout)
        self.create_iavf(self.max_vf_num)
        self.launch_testpmd("--rxq=4 --txq=4")
        self.config_testpmd()
        self.rte_flow_process(max_vfs_4_queues)
        self.dut.close_session(session_last)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.pmd_output.execute_cmd("quit", "#")
        self.dut.kill_all()
        self.destroy_iavf()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.session_list)
        self.dut.kill_all()
