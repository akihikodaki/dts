# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2021 Intel Corporation
#

import re
import time

from scapy.all import *

import tests.rte_flow_common as rfc
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.utils import GREEN, RED

LAUNCH_QUEUE = 16

tv_mac_ipv4_frag_fdir_queue_index = {
    "name": "tv_mac_ipv4_frag_fdir_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions queue index 1 / mark / end",
    "scapy_str": {
        "matched": ["Ether(dst='00:11:22:33:55:66')/IP(id=47750)/Raw('X'*666)"],
        "unmatched": [
            "Ether(dst='00:11:22:33:55:66')/IP()/Raw('X'*666)",
            "Ether(dst='00:11:22:33:55:66')/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666)",
        ],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": 1, "mark_id": 0},
}

tv_mac_ipv4_frag_fdir_rss_queues = {
    "name": "tv_mac_ipv4_frag_fdir_rss_queues",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions rss queues 2 3 end / mark / end",
    ],
    "scapy_str": {
        "matched": ["Ether(dst='00:11:22:33:55:66')/IP(id=47750)/Raw('X'*666)"],
        "unmatched": [
            "Ether(dst='00:11:22:33:55:66')/IP()/Raw('X'*666)",
            "Ether(dst='00:11:22:33:55:66')/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666)",
        ],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": [2, 3], "mark_id": 0},
}

tv_mac_ipv4_frag_fdir_passthru = {
    "name": "tv_mac_ipv4_frag_fdir_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions passthru / mark / end",
    "scapy_str": {
        "matched": ["Ether(dst='00:11:22:33:55:66')/IP(id=47750)/Raw('X'*666)"],
        "unmatched": [
            "Ether(dst='00:11:22:33:55:66')/IP()/Raw('X'*666)",
            "Ether(dst='00:11:22:33:55:66')/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666)",
        ],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 0, "rss": True},
}

tv_mac_ipv4_frag_fdir_drop = {
    "name": "tv_mac_ipv4_frag_fdir_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions drop / mark / end",
    "scapy_str": {
        "matched": ["Ether(dst='00:11:22:33:55:66')/IP(id=47750)/Raw('X'*666)"],
        "unmatched": [
            "Ether(dst='00:11:22:33:55:66')/IP()/Raw('X'*666)",
            "Ether(dst='00:11:22:33:55:66')/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666)",
        ],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "drop": True},
}

tv_mac_ipv4_frag_fdir_mark_rss = {
    "name": "tv_mac_ipv4_frag_fdir_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions mark / rss / end",
    "scapy_str": {
        "matched": ["Ether(dst='00:11:22:33:55:66')/IP(id=47750)/Raw('X'*666)"],
        "unmatched": [
            "Ether(dst='00:11:22:33:55:66')/IP()/Raw('X'*666)",
            "Ether(dst='00:11:22:33:55:66')/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666)",
        ],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 0, "rss": True},
}

tv_mac_ipv4_frag_fdir_mark = {
    "name": "tv_mac_ipv4_frag_fdir_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions mark id 1 / end",
    "scapy_str": {
        "matched": ["Ether(dst='00:11:22:33:55:66')/IP(id=47750)/Raw('X'*666)"],
        "unmatched": [
            "Ether(dst='00:11:22:33:55:66')/IP()/Raw('X'*666)",
            "Ether(dst='00:11:22:33:55:66')/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666)",
        ],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 1},
}

tvs_mac_ipv4_fragment_fdir = [
    tv_mac_ipv4_frag_fdir_queue_index,
    tv_mac_ipv4_frag_fdir_rss_queues,
    tv_mac_ipv4_frag_fdir_passthru,
    tv_mac_ipv4_frag_fdir_drop,
    tv_mac_ipv4_frag_fdir_mark_rss,
    tv_mac_ipv4_frag_fdir_mark,
]

tvs_mac_ipv4_fragment_fdir_l3src = [
    eval(
        str(element)
        .replace("mac_ipv4_frag_fdir", "mac_ipv4_frag_fdir_l3src")
        .replace("ipv4 fragment_offset", "ipv4 src is 192.168.1.1 fragment_offset")
        .replace("IP(id=47750)", "IP(id=47750, src='192.168.1.1')")
    )
    for element in tvs_mac_ipv4_fragment_fdir
]

tvs_mac_ipv4_fragment_fdir_l3dst = [
    eval(
        str(element)
        .replace("mac_ipv4_frag_fdir", "mac_ipv4_frag_fdir_l3dst")
        .replace("ipv4 fragment_offset", "ipv4 dst is 192.168.1.2 fragment_offset")
        .replace("IP(id=47750)", "IP(id=47750, dst='192.168.1.2')")
    )
    for element in tvs_mac_ipv4_fragment_fdir
]

tvs_mac_ipv4_frag_fdir_with_l3 = (
    tvs_mac_ipv4_fragment_fdir_l3src + tvs_mac_ipv4_fragment_fdir_l3dst
)

tv_mac_ipv6_frag_fdir_queue_index = {
    "name": "tv_mac_ipv6_frag_fdir_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext frag_data spec 0x0001 frag_data mask 0x0001 / end actions queue index 1 / mark / end",
    "scapy_str": {
        "matched": [
            "Ether(dst='00:11:22:33:55:66')/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666)"
        ],
        "unmatched": [
            "Ether(dst='00:11:22:33:55:66')/IPv6()/Raw('X'*666)",
            "Ether(dst='00:11:22:33:55:66')/IP(id=47750)/Raw('X'*666)",
        ],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": 1, "mark_id": 0},
}

tv_mac_ipv6_frag_fdir_rss_queues = {
    "name": "tv_mac_ipv6_frag_fdir_rss_queues",
    "rule": [
        "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext frag_data spec 0x0001 frag_data mask 0x0001 / end actions rss queues 2 3 end / mark / end",
    ],
    "scapy_str": {
        "matched": [
            "Ether(dst='00:11:22:33:55:66')/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666)"
        ],
        "unmatched": [
            "Ether(dst='00:11:22:33:55:66')/IPv6()/Raw('X'*666)",
            "Ether(dst='00:11:22:33:55:66')/IP(id=47750)/Raw('X'*666)",
        ],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": [2, 3], "mark_id": 0},
}

tv_mac_ipv6_frag_fdir_passthru = {
    "name": "tv_mac_ipv6_frag_fdir_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext frag_data spec 0x0001 frag_data mask 0x0001 / end actions passthru / mark / end",
    "scapy_str": {
        "matched": [
            "Ether(dst='00:11:22:33:55:66')/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666)"
        ],
        "unmatched": [
            "Ether(dst='00:11:22:33:55:66')/IPv6()/Raw('X'*666)",
            "Ether(dst='00:11:22:33:55:66')/IP(id=47750)/Raw('X'*666)",
        ],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 0, "rss": True},
}

tv_mac_ipv6_frag_fdir_drop = {
    "name": "tv_mac_ipv6_frag_fdir_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext frag_data spec 0x0001 frag_data mask 0x0001 / end actions drop / mark / end",
    "scapy_str": {
        "matched": [
            "Ether(dst='00:11:22:33:55:66')/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666)"
        ],
        "unmatched": [
            "Ether(dst='00:11:22:33:55:66')/IPv6()/Raw('X'*666)",
            "Ether(dst='00:11:22:33:55:66')/IP(id=47750)/Raw('X'*666)",
        ],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "drop": True},
}

tv_mac_ipv6_frag_fdir_mark_rss = {
    "name": "tv_mac_ipv6_frag_fdir_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext frag_data spec 0x0001 frag_data mask 0x0001 / end actions mark / rss / end",
    "scapy_str": {
        "matched": [
            "Ether(dst='00:11:22:33:55:66')/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666)"
        ],
        "unmatched": [
            "Ether(dst='00:11:22:33:55:66')/IPv6()/Raw('X'*666)",
            "Ether(dst='00:11:22:33:55:66')/IP(id=47750)/Raw('X'*666)",
        ],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 0, "rss": True},
}

tv_mac_ipv6_frag_fdir_mark = {
    "name": "tv_mac_ipv6_frag_fdir_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext frag_data spec 0x0001 frag_data mask 0x0001 / end actions mark id 1 / end",
    "scapy_str": {
        "matched": [
            "Ether(dst='00:11:22:33:55:66')/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666)"
        ],
        "unmatched": [
            "Ether(dst='00:11:22:33:55:66')/IPv6()/Raw('X'*666)",
            "Ether(dst='00:11:22:33:55:66')/IP(id=47750)/Raw('X'*666)",
        ],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 1},
}

tvs_mac_ipv6_fragment_fdir = [
    tv_mac_ipv6_frag_fdir_queue_index,
    tv_mac_ipv6_frag_fdir_rss_queues,
    tv_mac_ipv6_frag_fdir_passthru,
    tv_mac_ipv6_frag_fdir_drop,
    tv_mac_ipv6_frag_fdir_mark_rss,
    tv_mac_ipv6_frag_fdir_mark,
]

tvs_mac_ipv6_fragment_fdir_l3src = [
    eval(
        str(element)
        .replace("mac_ipv6_frag_fdir", "mac_ipv6_frag_fdir_l3src")
        .replace("/ ipv6 /", "/ ipv6 src is 2001::1 /")
        .replace("IPv6()", "IPv6(src='2001::1')")
    )
    for element in tvs_mac_ipv6_fragment_fdir
]

tvs_mac_ipv6_fragment_fdir_l3dst = [
    eval(
        str(element)
        .replace("mac_ipv6_frag_fdir", "mac_ipv6_frag_fdir_l3dst")
        .replace("/ ipv6 /", "/ ipv6 dst is 2001::2 /")
        .replace("IPv6()", "IPv6(dst='2001::2')")
    )
    for element in tvs_mac_ipv6_fragment_fdir
]

tvs_mac_ipv6_frag_fdir_with_l3 = (
    tvs_mac_ipv6_fragment_fdir_l3src + tvs_mac_ipv6_fragment_fdir_l3dst
)

tv_rss_basic_packets = {
    "ipv4_rss_fragment": "Ether(src='00:11:22:33:44:55', dst='00:11:22:33:55:66')/IP(src='192.168.6.11', dst='10.11.12.13', id=47750)/Raw('X'*666)",
    "ipv6_rss_fragment": "Ether(src='00:11:22:33:44:55', dst='00:11:22:33:55:66')/IPv6(src='CDCD:910A:2222:5498:8475:1111:3900:1537', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/IPv6ExtHdrFragment(id=47750)/Raw('X'*666)",
}

tv_mac_ipv4_fragment_rss = {
    "sub_casename": "tv_mac_ipv4_fragment_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-frag end key_len 0 queues end / end",
    "port_id": 0,
    "test": [
        {
            "send_packet": tv_rss_basic_packets["ipv4_rss_fragment"],
            "action": {"save_hash": "ipv4"},
        },
        {
            "send_packet": tv_rss_basic_packets["ipv4_rss_fragment"].replace(
                "192.168.6.11", "192.168.6.12"
            ),
            "action": {"check_hash_different": "ipv4"},
        },
        {
            "send_packet": tv_rss_basic_packets["ipv4_rss_fragment"].replace(
                "10.11.12.13", "10.11.12.14"
            ),
            "action": {"check_hash_different": "ipv4"},
        },
        {
            "send_packet": tv_rss_basic_packets["ipv4_rss_fragment"].replace(
                "id=47750", "id=47751"
            ),
            "action": {"check_hash_different": "ipv4"},
        },
        {
            "send_packet": "Ether()/IPv6()/IPv6ExtHdrFragment(id=47751)/Raw('X'*666)",
            "action": {"check_no_hash": "ipv4"},
        },
    ],
    "post-test": [
        {
            "send_packet": tv_rss_basic_packets["ipv4_rss_fragment"],
            "action": {"check_no_hash": "ipv4"},
        },
    ],
}

tv_mac_ipv6_fragment_rss = {
    "sub_casename": "tv_mac_ipv6_fragment_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext / end actions rss types ipv6-frag end key_len 0 queues end / end",
    "port_id": 0,
    "test": [
        {
            "send_packet": tv_rss_basic_packets["ipv6_rss_fragment"],
            "action": {"save_hash": "ipv6"},
        },
        {
            "send_packet": tv_rss_basic_packets["ipv6_rss_fragment"].replace(
                "3900:1537", "3900:1538"
            ),
            "action": {"check_hash_different": "ipv6"},
        },
        {
            "send_packet": tv_rss_basic_packets["ipv6_rss_fragment"].replace(
                "3900:2020", "3900:2021"
            ),
            "action": {"check_hash_different": "ipv6"},
        },
        {
            "send_packet": tv_rss_basic_packets["ipv6_rss_fragment"].replace(
                "id=47750", "id=47751"
            ),
            "action": {"check_hash_different": "ipv6"},
        },
        {
            "send_packet": "Ether()/IP(id=47750)/Raw('X'*666)",
            "action": {"check_no_hash": "ipv6"},
        },
    ],
    "post-test": [
        {
            "send_packet": tv_rss_basic_packets["ipv6_rss_fragment"],
            "action": {"check_no_hash": "ipv6"},
        },
    ],
}


class TestICEIavfIpFragmentRteFlow(TestCase):
    def set_up_all(self):
        self.ports = self.dut.get_ports(self.nic)

        # init pkt
        self.pkt = Packet()
        # set default app parameter
        self.pmd_out = PmdOutput(self.dut)
        self.tester_mac = self.tester.get_mac(0)
        self.tester_port0 = self.tester.get_local_port(self.ports[0])
        self.tester_iface0 = self.tester.get_interface(self.tester_port0)

        self.tester.send_expect("ifconfig {} up".format(self.tester_iface0), "# ")
        self.param = "--rxq={} --txq={} --disable-rss --txd=384 --rxd=384".format(
            LAUNCH_QUEUE, LAUNCH_QUEUE
        )
        self.param_fdir = "--rxq={} --txq={}".format(LAUNCH_QUEUE, LAUNCH_QUEUE)
        self.cores = self.dut.get_core_list("1S/4C/1T")
        self.setup_1pf_vfs_env()

        self.ports_pci = [self.dut.ports_info[self.ports[0]]["pci"]]

        self.rssprocess = rfc.RssProcessing(
            self, self.pmd_out, [self.tester_iface0], LAUNCH_QUEUE, ipfrag_flag=True
        )
        self.fdirprocess = rfc.FdirProcessing(
            self, self.pmd_out, [self.tester_iface0], LAUNCH_QUEUE, ipfrag_flag=True
        )

    def set_up(self):
        pass

    def setup_1pf_vfs_env(self):
        """
        create vf and set vf mac
        """
        self.dut.bind_interfaces_linux("ice")
        self.pf_interface = self.dut.ports_info[0]["intf"]
        self.dut.send_expect("ifconfig {} up".format(self.pf_interface), "# ")
        self.dut.generate_sriov_vfs_by_port(self.ports[0], 1, driver=self.kdriver)
        self.dut.send_expect(
            "ip link set {} vf 0 mac 00:11:22:33:55:66".format(self.pf_interface), "# "
        )
        self.vf_port = self.dut.ports_info[0]["vfs_port"]
        self.verify(len(self.vf_port) != 0, "VF create failed")
        self.vf_driver = self.get_suite_cfg()["vf_driver"]
        if self.vf_driver is None:
            self.vf_assign_method = "vfio-pci"
        self.vf_port[0].bind_driver(self.vf_driver)

        self.vf_ports_pci = [self.vf_port[0].pci]

    def launch_testpmd(self, param_fdir=False):
        """
        start testpmd with fdir or rss param, and pf or vf

        :param param_fdir: True: Fdir param/False: rss param
        """
        if param_fdir == True:
            self.pmd_out.start_testpmd(
                cores=self.cores, ports=self.vf_ports_pci, param=self.param_fdir
            )
        else:
            self.pmd_out.start_testpmd(
                cores=self.cores, ports=self.vf_ports_pci, param=self.param
            )
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("set verbose 1", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

    def destroy_testpmd_and_vf(self):
        """
        quit testpmd
        if vf testpmd, destroy the vfs and set vf_flag = false
        """
        for port_id in self.ports:
            self.dut.destroy_sriov_vfs_by_port(port_id)

    def tear_down(self):
        self.dut.send_expect("quit", "# ")
        self.dut.kill_all()

    def tear_down_all(self):
        self.destroy_testpmd_and_vf()
        self.dut.kill_all()

    def test_iavf_mac_ipv4_frag_fdir(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_fragment_fdir)

    def test_iavf_mac_ipv6_frag_fdir(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_fragment_fdir)

    def test_iavf_mac_ipv4_frag_fdir_with_l3(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_frag_fdir_with_l3)

    def test_iavf_mac_ipv6_frag_fdir_with_l3(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_frag_fdir_with_l3)

    def test_iavf_mac_ipv4_frag_rss(self):
        self.launch_testpmd(param_fdir=False)
        self.rssprocess.handle_rss_distribute_cases(tv_mac_ipv4_fragment_rss)

    def test_iavf_mac_ipv6_frag_rss(self):
        self.launch_testpmd(param_fdir=False)
        self.rssprocess.handle_rss_distribute_cases(tv_mac_ipv6_fragment_rss)

    def test_exclusive_validation(self):
        result = True
        result_list = []
        rule_list_fdir = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions queue index 2 / end",
        ]
        pkt_fdir = ["Ether()/IP(src='192.168.0.20', id=47750)/Raw('X'*666)"]
        p = re.compile(r"port\s+%s/queue\s+(\d+):\s+received\s+(\d+)\s+packets" % 0)

        self.logger.info("Subcase 1: exclusive validation fdir rule")
        self.launch_testpmd(param_fdir=True)
        try:
            self.rssprocess.create_rule(rule_list_fdir)
        except Exception as e:
            self.logger.warning("Subcase 1 failed: %s" % e)
            result = False
        out = self.fdirprocess.send_pkt_get_output(pkt_fdir)
        res = p.findall(out)
        for queue in res:
            if queue[0][0].strip() != "2":
                result = False
                self.logger.error("Error: queue index {} != '2'".format(queue[0][0]))
                continue
        result_list.append(result)
        self.dut.send_expect("quit", "# ")
        self.logger.info("*********subcase test result %s" % result_list)

        self.logger.info("Subcase 2: exclusive validation fdir rule")
        result = True
        self.launch_testpmd(param_fdir=True)
        try:
            self.rssprocess.create_rule(rule_list_fdir[::-1])
        except Exception as e:
            self.logger.warning("Subcase 2 failed: %s" % e)
            result = False
        out = self.fdirprocess.send_pkt_get_output(pkt_fdir)
        res = p.findall(out)
        for queue in res:
            if queue[0][0].strip() != "2":
                result = False
                self.logger.error("Error: queue index {} != '2'".format(queue[0][0]))
                continue
        result_list.append(result)
        self.dut.send_expect("quit", "# ")
        self.logger.info("*********subcase test result %s" % result_list)

        self.logger.info("Subcase 3: exclusive validation rss rule")
        result = True
        self.launch_testpmd()
        rule_list_rss = [
            "flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-frag end key_len 0 queues end / end",
        ]
        pkt_Rss = [
            "Ether()/IP(id=47750)/Raw('X'*666)",
            "Ether()/IP(id=47751)/Raw('X'*666)",
        ]
        try:
            self.rssprocess.create_rule(rule_list_rss)
        except Exception as e:
            self.logger.warning("Subcase 3 failed: %s" % e)
            result = False
        hashes1, queues1 = self.rssprocess.send_pkt_get_hash_queues(pkts=pkt_Rss[0])
        hashes2, queues2 = self.rssprocess.send_pkt_get_hash_queues(pkts=pkt_Rss[1])
        if hashes1[0] != hashes1[1] and hashes2[0] != hashes2[1]:
            result = False
            self.logger.error("hash value is incorrect")
        if hashes1[0] == hashes2[0]:
            result = False
            self.logger.error("hash value is incorrect")
        result_list.append(result)
        self.dut.send_expect("quit", "# ")
        self.logger.info("*********subcase test result %s" % result_list)

        self.logger.info("Subcase 4: exclusive validation rss rule")
        result = True
        self.launch_testpmd()
        try:
            self.rssprocess.create_rule(rule_list_rss[::-1])
        except Exception as e:
            self.logger.warning("Subcase 3 failed: %s" % e)
        hashes1, queues1 = self.rssprocess.send_pkt_get_hash_queues(pkts=pkt_Rss[0])
        hashes2, queues2 = self.rssprocess.send_pkt_get_hash_queues(pkts=pkt_Rss[1])
        if hashes1[0] != hashes1[1] and hashes2[0] != hashes2[1]:
            result = False
            self.logger.error("hash value is incorrect")
        if hashes1[0] == hashes2[0]:
            result = False
            self.logger.error("hash value is incorrect")
        result_list.append(result)
        self.dut.send_expect("quit", "# ")
        self.logger.info("*********subcase test result %s" % result_list)
        self.verify(all(result_list) is True, "sub-case failed {}".format(result_list))

    def test_negative_case(self):
        negative_rules = [
            "flow create 0 ingress pattern eth / ipv6 packet_id is 47750 fragment_offset spec 0x2000 fragment_offset last 0x1fff fragment_offset mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 packet_id is 47750 fragment_offset spec 0x2000 fragment_offset last 0x1fff fragment_offset mask 0xffff / end actions queue index 300 / end",
            "flow create 0 ingress pattern eth / ipv4 packet_id is 0x10000 fragment_offset spec 0x2000 fragment_offset last 0x1fff fragment_offset mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 packet_id is 47750 fragment_offset spec 0x2 fragment_offset last 0x1fff fragment_offset mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 packet_id is 47750 fragment_offset spec 0x2000 fragment_offset last 0x1 fragment_offset mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 packet_id is 47750 fragment_offset spec 0x2000 fragment_offset last 0x1fff fragment_offset mask 0xf / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 packet_id is 47750 fragment_offset last 0x1fff fragment_offset mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 packet_id is 47750 fragment_offset spec 0x2000 fragment_offset mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 packet_id is 47750 fragment_offset spec 0x2000 fragment_offset last 0x1fff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 packet_id is 0x10000 / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 packet_id is 47750 / end actions queue index 300 / end",
            "flow create 0 ingress pattern eth / ipv4 packet_id spec 0xfff packet_id last 0x0 packet_id mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 packet_id last 0xffff packet_id mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 packet_id spec 0 packet_id mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 packet_id spec 0 packet_id last 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / ipv6_frag_ext packet_id is 47750 frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id is 47750 frag_data spec 0xfff8 frag_data last 0x0001 frag_data mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id is 47750 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id is 47750 frag_data spec 0x0001 frag_data mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id is 47750 frag_data spec 0x0001 frag_data last 0xfff8 / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id is 47750 frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 300 / end",
            "flow create 0 ingress pattern eth / ipv4 / ipv6_frag_ext packet_id spec 0 packet_id last 0xffff packet_id mask 0xffff frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id spec 0xffff packet_id last 0x0 packet_id mask 0xffff frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id spec 0 packet_id last 0xffff packet_id mask 0xffff frag_data spec 0xfff8 frag_data last 0x0001 frag_data mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / packet_id last 0xffff packet_id mask 0xffff frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id spec 0 packet_id mask 0xffff frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id spec 0 packet_id last 0xffff frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id spec 0 packet_id last 0xffff packet_id mask 0xffff frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id spec 0 packet_id last 0xffff packet_id mask 0xffff frag_data spec 0x0001 frag_data last 0xfff8 / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id spec 0 packet_id last 0xffff packet_id mask 0xffff frag_data spec 0x0001 frag_data mask 0xffff / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / ipv6_frag_ext packet_id is 47750 / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id is 0x10000 / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv4-frag end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / ipv6_frag_ext / end actions rss types ipv6-frag end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext / end actions rss types ipv4-frag end key_len 0 queues end / end",
        ]
        self.launch_testpmd()
        self.rssprocess.create_rule(negative_rules, check_stats=False)
