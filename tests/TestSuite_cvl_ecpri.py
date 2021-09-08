import re
from packet import Packet
from pmd_output import PmdOutput
from test_case import TestCase
import rte_flow_common as rfc
import utils
from utils import GREEN, RED
import time

Mac_list = ['00:11:22:33:44:55', '00:11:22:33:44:11', '00:11:22:33:44:22', '00:11:22:33:44:33']

pkt_lst = ["Ether(dst='{}')/IP()/UDP(dport={})/Raw(\'\\x10\\x00\')",
             "Ether(dst='{}')/IP()/UDP(dport={})/Raw(\'\\x10\\x02\')/Raw('x'*11)/Raw(\'\\x00\')",
             "Ether(dst='{}')/IP()/UDP(dport={})/Raw(\'\\x10\\x02')/Raw('x'*11)/Raw(\'\\x01')",
             "Ether(dst='{}')/IP()/UDP(dport={})/Raw(\'\\x10\\x02\')/Raw('x'*11)/Raw(\'\\x03\')",
             "Ether(dst='{}')/IP()/UDP(dport={})/Raw(\'\\x10\\x02\')/Raw('x'*11)/Raw(\'\\x05\')",
             "Ether(dst='{}')/IP()/UDP(dport={})/Raw(\'\\x10\\x02\')/Raw('x'*11)/Raw(\'\\x06\')",
             "Ether(dst='{}')/IP()/UDP(dport={})/Raw(\'\\x10\\x02\')/Raw('x'*11)/Raw(\'\\x07\')",
             "Ether(dst='{}')/IP()/UDP(dport={})/Raw(\'\\x10\\x02\')/Raw('x'*11)/Raw(\'\\x08\')",
             "Ether(dst='{}')/IP()/UDP(dport={})/Raw(\'\\x10\\x05\')",
             "Ether(dst='{}')/IP()/UDP(dport={})/Raw(\'\\x10\\x06\')"
             ]

ptype_match_lst = ['ptype=' + str(i) for i in range(372, 382)]
ptype_nomatch_lst = ['ptype=24'] * 10

# eCPRI over Ethernet header data.
eCPRI_over_Ethernet_rule = "flow create 1 ingress pattern eth / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end"
over_eth_header_packets = {
    'match': ["Ether(dst='00:11:22:33:44:11', type=0xAEFE)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\x45\')"],
    'unmatched': ["Ether(dst='00:11:22:33:44:11', type=0xAEFE)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\x46\')"]
}

tv_over_eth_queue_index = {
    "name": "test_eth_queue_index",
    "rule": "flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions queue index 3 / mark id 1 / end",
    "scapy_str": over_eth_header_packets,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 1, "queue": 3, "mark_id": 1, 'rxq': 16},
    "send_port": {"port_id": 0}
}

tv_over_eth_rss_queues = {
    "name": "test_eth_rss_queues",
    "rule": "flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions rss queues 5 6 end / mark id 2 / end",
    "scapy_str": over_eth_header_packets,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 1, "queue": [5, 6], "mark_id": 2, 'rxq': 16},
    "send_port": {"port_id": 0}
}

tv_over_eth_drop = {
    "name": "test_eth_drop",
    "rule": "flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions drop / end",
    "scapy_str": over_eth_header_packets,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 1, "drop": True, 'rxq': 16},
    "send_port": {"port_id": 0}
}

tv_over_eth_passthru = {
    "name": "test_eth_passthru",
    "rule": "flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions passthru / mark id 1 / end",
    "scapy_str": over_eth_header_packets,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 1, "rss": True, "mark_id": 1, 'rxq': 16},
    "send_port": {"port_id": 0}
}

tv_over_eth_mark_rss = {
    "name": "test_eth_mark_rss",
    "rule": "flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions mark / rss / end",
    "scapy_str": over_eth_header_packets,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 1, "mark_id": 0, "rss": True, 'rxq': 16},
    "send_port": {"port_id": 0}
}

tv_over_eth_mark = {
    "name": "test_eth_mark",
    "rule": "flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions mark / end",
    "scapy_str": over_eth_header_packets,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 1, "mark_id": 0, "rss": True, 'rxq': 16},
    "send_port": {"port_id": 0}
}

# eCPRI over IP/UDP header data.
eCPRI_over_IP_UDP_rule = "flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end actions rss types ecpri end key_len 0 queues end / end"
over_ip_udp_header_packets = {
    'match': ["Ether(dst='00:11:22:33:44:11')/IP()/UDP(dport=0x5123)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\x45\')"],
    'unmatched': ["Ether(dst='00:11:22:33:44:11')/IP()/UDP(dport=0x5123)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\x46\')"]
}

tv_over_ip_udp_queue_index = {
    "name": "test_ip_udp_queue_index",
    "rule": "flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions queue index 2 / mark / end",
    "scapy_str": over_ip_udp_header_packets,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 1, "queue": 2, "mark_id": 0, 'rxq': 16},
    "send_port": {"port_id": 0}
}

tv_over_ip_udp_rss_queues = {
    "name": "test_ip_udp_rss_queues",
    "rule": "flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions rss queues 5 6 end / mark id 2 / end",
    "scapy_str": over_ip_udp_header_packets,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 1, "queue": [5, 6], "mark_id": 2, 'rxq': 16},
    "send_port": {"port_id": 0}
}

tv_over_ip_udp_drop = {
    "name": "test_ip_udp_drop",
    "rule": "flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions drop / end",
    "scapy_str": over_ip_udp_header_packets,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 1, "drop": True, 'rxq': 16},
    "send_port": {"port_id": 0}
}

tv_over_ip_udp_passthru = {
    "name": "test_ip_udp_passthru",
    "rule": "flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions passthru / mark id 1 / end",
    "scapy_str": over_ip_udp_header_packets,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 1, "rss": True, "mark_id": 1, 'rxq': 16},
    "send_port": {"port_id": 0}
}

tv_over_ip_udp_mark_rss = {
    "name": "test_ip_udp_mark_rss",
    "rule": "flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions mark / rss / end",
    "scapy_str": over_ip_udp_header_packets,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 1, "mark_id": 0, "rss": True, 'rxq': 16},
    "send_port": {"port_id": 0}
}

tv_over_ip_udp_mark = {
    "name": "test_ip_udp_mark",
    "rule": "flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end actions mark / end",
    "scapy_str": over_ip_udp_header_packets,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 1, "mark_id": 0, "rss": True, 'rxq': 16},
    "send_port": {"port_id": 0}
}

tv_over_eth = [tv_over_eth_queue_index, tv_over_eth_rss_queues, tv_over_eth_drop, tv_over_eth_passthru, tv_over_eth_mark_rss, tv_over_eth_mark]

tv_over_ip_udp = [tv_over_ip_udp_queue_index, tv_over_ip_udp_rss_queues, tv_over_ip_udp_drop, tv_over_ip_udp_passthru, tv_over_ip_udp_mark_rss, tv_over_ip_udp_mark]

class TestCVLEcpri(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        prerequisites.
        """
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for testing")
        # Verify that enough threads are available
        cores = self.dut.get_core_list("1S/4C/1T")
        self.verify(cores is not None, "Insufficient cores for speed testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.tester_port0 = self.tester.get_local_port(self.dut_ports[0])
        self.tester_port1 = self.tester.get_local_port(self.dut_ports[1])
        self.tester_iface0 = self.tester.get_interface(self.tester_port0)
        self.tester_iface1 = self.tester.get_interface(self.tester_port1)

        self.used_dut_port = self.dut_ports[0]
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.file_path = './drivers/net/iavf/iavf_rxtx.c'
        self.compile_dpdk()
        self.vf_flag = False
        self.create_iavf()

        self.pass_flag = 'passed'
        self.fail_flag = 'failed'
        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)
        self.right_ecpri = '0x5123'
        self.wrong_ecpri = '0x5121'

        self.new_session = self.dut.create_session(name="self.new_session")

    def set_up(self):
        """
        Run before each test case.
        """
        self.new_session.send_expect("ip link set {} vf 0 trust on".format(self.pf_interface), "# ", timeout=10)
        self.new_session.send_expect("ip link set {} vf 0 mac 00:11:22:33:44:00".format(self.pf_interface), "# ", timeout=10)
        self.launch_testpmd()
        self.pkt = Packet()

    def create_iavf(self):
        if self.vf_flag is False:
            self.dut.bind_interfaces_linux('ice')
            self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 4)
            self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]['vfs_port']
            self.vf_flag = True

            try:
                for i in range(len(self.sriov_vfs_port)):
                    if i != len(self.sriov_vfs_port):
                        self.sriov_vfs_port[i].bind_driver(self.drivername)
                    self.dut.send_expect("ip link set %s vf %s mac %s" % (self.pf_interface, i, Mac_list[i]), "# ")

            except Exception as e:
                self.destroy_iavf()
                raise Exception(e)

    def destroy_iavf(self):
        if self.vf_flag is True:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.vf_flag = False

    def launch_testpmd(self):
        eal_param = " -a {},cap=dcf -a {} -a {}".format(self.sriov_vfs_port[0].pci, self.sriov_vfs_port[1].pci,
                                                                   self.sriov_vfs_port[2].pci)
        param = " --rxq=16 --txq=16"
        out = self.pmd_output.start_testpmd(cores=[0, 1, 2, 3], eal_param=eal_param, param=param, socket=self.ports_socket)
        # check the VF0 driver is net_ice_dcf
        self.check_dcf_status(out, stats=True)
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("start")

    def check_dcf_status(self, out_testpmd, stats=True):
        """
        check if request for DCF is accepted.
        """
        if stats:
            self.verify("Failed to init DCF parent adapter" not in out_testpmd, "request for DCF is rejected.")
            out_portinfo = self.dut.send_expect("show port info 0", "testpmd> ", 15)
            self.verify("net_ice_dcf" in out_portinfo, "request for DCF is rejected.")
        else:
            self.verify("Failed to init DCF parent adapter" in out_testpmd, "request for DCF is accepted.")
            out_portinfo = self.dut.send_expect("show port info 0", "testpmd> ", 15)
            self.verify("net_ice_dcf" not in out_portinfo, "request for DCF is accepted.")

    def test_add_and_delete_eCPRI_port_config_in_DCF(self):
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri {}".format(self.right_ecpri))
        self.send_and_verify(Mac_list[1], self.right_ecpri, if_match=True)
        self.send_and_verify(Mac_list[1], self.wrong_ecpri, if_match=False)
        self.send_and_verify(Mac_list[2], self.right_ecpri, if_match=True)
        # remove rule and test
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port rm ecpri {}".format(self.right_ecpri))

        self.send_and_verify(Mac_list[1], self.right_ecpri, if_match=False)

    def test_eCPRI_port_config_when_DCF_exit_reset(self):
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri {}".format(self.right_ecpri))
        self.pmd_output.execute_cmd("quit", expected="#")
        self.launch_testpmd()
        self.send_and_verify(Mac_list[1], self.right_ecpri, if_match=False)
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri {}".format(self.right_ecpri))
        # use new mac to test
        new_mac = "00:11:22:33:44:66"
        self.new_session.send_expect("ip link set {} vf 0 mac {}".format(self.pf_interface, new_mac), "#", timeout=10)
        self.send_and_verify(Mac_list[1], self.right_ecpri, if_match=False)
        self.pmd_output.execute_cmd("quit", expected="#")
        # set port vf 0 trust off and test
        self.launch_testpmd()
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri {}".format(self.right_ecpri))
        self.new_session.send_expect("ip link set {} vf 0 trust off".format(self.pf_interface), "#", timeout=10)
        self.send_and_verify(Mac_list[1], self.right_ecpri, if_match=False)

    def test_DCF_port_config_and_linux_port_config(self):
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri {}".format(self.right_ecpri))
        self.new_session.send_expect("dmesg -c", "#")
        self.new_session.send_expect("ip link add vx0 type vxlan id 100 local 1.1.1.1 remote "
                                "2.2.2.2 dev {} dstport 0x1234".format(self.pf_interface), "#")
        self.new_session.send_expect("ifconfig vx0 up", "#")
        self.new_session.send_expect("ifconfig vx0 down", "#")
        out = self.new_session.send_expect("dmesg", "#")
        self.verify("Cannot config tunnel, the capability is used by DCF" in out, "port can used by another thread!")
        # delete eCPRI port config and test
        self.new_session.send_expect("dmesg -c", "#")
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port rm ecpri {}".format(self.right_ecpri))
        self.new_session.send_expect("ifconfig vx0 up", "#")
        self.new_session.send_expect("ifconfig vx0 down", "# ")
        out = self.new_session.send_expect("dmesg", "#")
        self.verify("Cannot config tunnel, the capability is used by DCF" not in out, "port can't used by another thread!")
        self.pmd_output.execute_cmd("quit", "#")
        # do ecpri test
        self.launch_testpmd()
        self.new_session.send_expect("ip link add vx0 type vxlan id 100 local 1.1.1.1 remote "
                                "2.2.2.2 dev {} dstport 0x1234".format(self.pf_interface), "#")
        self.new_session.send_expect("ifconfig vx0 up", "#")
        out = self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri {}".format(self.right_ecpri))
        self.verify("ice_dcf_send_aq_cmd(): No response (201 times) or return failure (desc: -63 / buff: -63)" in out,
                    "test fail")
        # set vx0 down and test
        self.new_session.send_expect("ifconfig vx0 down", "#")
        out = self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri {}".format(self.right_ecpri))
        self.verify("ice_dcf_send_aq_cmd(): No response (201 times) or return failure (desc: -63 / buff: -63)"
                    not in out, "test fail")

    def test_negative_eCPRI_port_config_in_DCF(self):
        ecpri_and_expect_dic = {"1": "Operation not supported",
                                "5": "Invalid port",
                                "15": "Invalid port",
                                "a": "Bad arguments"
                                }
        # set wrong port to test
        for ecpri in ecpri_and_expect_dic.keys():
            out = self.pmd_output.execute_cmd("port config {} udp_tunnel_port add ecpri {}".format(ecpri, self.right_ecpri))
            self.verify(ecpri_and_expect_dic[ecpri] in out, "test fail")
        # set an invalid ecpri to test
        ecpri_and_expect_dic = {"ffff": "Bad arguments",
                                "65536": "Bad arguments"}

        for ecpri in ecpri_and_expect_dic.keys():
            out = self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri {}".format(ecpri))
            self.verify(ecpri_and_expect_dic[ecpri] in out, "test fail")
            if ecpri == "0":
                # test remove an invalid ecpri
                out = self.pmd_output.execute_cmd("port config 0 udp_tunnel_port rm ecpri {}".format(ecpri))
                self.verify("Operation not permitted" in out, "test fail")

    def test_rss_for_udp_ecpri(self):
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri {}".format(self.right_ecpri))
        self.pmd_output.execute_cmd("flow validate 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / "
                                    "end actions rss types ecpri end key_len 0 queues end / end")
        self.pmd_output.execute_cmd("flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / "
                                    "end actions rss types ecpri end key_len 0 queues end / end")
        tag_lst = ['x45', 'x46', 'x47']
        pkt_str = "Ether(dst='{}')/IP()/UDP(dport=0x5123)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')".format(
            Mac_list[1])
        data_lst = self.get_receive_lst(tag_lst, [pkt_str])
        hash_lst = [i.get('RSS hash') for i in data_lst]
        self.verify(len(set(hash_lst)) == len(tag_lst) == len(set([i.get('queue') for i in data_lst])), "test fail, RSS hash is same.")
        # destroy rule and test
        self.pmd_output.execute_cmd("flow destroy 1 rule 0")
        out = self.pmd_output.execute_cmd("flow list 1")
        data_lst = self.get_receive_lst(tag_lst, [pkt_str], stats=False)
        hash_lst = [i.get('RSS hash') for i in data_lst]
        self.verify(len(hash_lst) == 0 or len(set(hash_lst)) == 1, "test fail, rule still worked.")

    def test_rss_for_eth_ecpri(self):
        self.dut.send_expect("quit", "# ")
        eal_param = " -a {} -a {}".format(self.sriov_vfs_port[0].pci, self.sriov_vfs_port[1].pci)
        param = " --rxq=16 --txq=16"
        self.pmd_output.start_testpmd(cores=[0, 1, 2, 3], eal_param=eal_param, param=param, socket=self.ports_socket)
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("start")
        self.pmd_output.execute_cmd("flow validate 1 ingress pattern eth / ecpri common type iq_data / "
                                    "end actions rss types ecpri end key_len 0 queues end / end")
        self.pmd_output.execute_cmd("flow create 1 ingress pattern eth / ecpri common type iq_data / end actions "
                                    "rss types ecpri end key_len 0 queues end / end")
        tag_lst = ['x45', 'x46', 'x47']
        pkt_str = "Ether(dst='{}', type=0xAEFE)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')".format(Mac_list[1])
        data_lst = self.get_receive_lst(tag_lst, [pkt_str])
        hash_lst = [i.get('RSS hash') for i in data_lst]
        self.verify(len(set(hash_lst)) == len(tag_lst), "test fail, RSS hash is same.")
        # destroy rule and test
        self.pmd_output.execute_cmd("flow destroy 1 rule 0")
        self.pmd_output.execute_cmd("flow list 1")
        data_lst = self.get_receive_lst(tag_lst, [pkt_str], stats=False)
        hash_lst = [i.get('RSS hash') for i in data_lst]
        self.verify(len(hash_lst) == 0 or len(set(hash_lst)) == 1, "test fail, rule still worked.")

    def test_rss_multirules_multiports(self):
        dst_mac_lst = Mac_list[1:3]
        tag_lst = ['x45', 'x46']
        module_pkt_lst = ["Ether(dst='{}')/IP()/UDP(dport=0x5123)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')",
                   "Ether(dst='{}', type=0xAEFE)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')"]
        rule_lst = ["flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end actions rss "
                    "types ecpri end key_len 0 queues end / end",
                    "flow create 1 ingress pattern eth / ecpri common type iq_data / end actions rss types ecpri end "
                    "key_len 0 queues end / end",
                    "flow create 2 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end actions rss types"
                    " ecpri end key_len 0 queues end / end",
                    "flow create 2 ingress pattern eth / ecpri common type iq_data / end actions rss types ecpri end "
                    "key_len 0 queues end / end"]
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri 0x5123")
        for rule in rule_lst:
            self.pmd_output.execute_cmd(rule)
        out_data = {}
        for dst_mac in dst_mac_lst:
            pkt_lst = [pkt.format(dst_mac) for pkt in module_pkt_lst]
            reta_line = self.get_receive_lst(tag_lst, pkt_lst)
            out_data.setdefault(dst_mac, reta_line)
        # verify
        for key in out_data.keys():
            hash_lst = [i.get('RSS hash') for i in out_data[key]]
            self.verify(len(set(hash_lst)) == 2 and None not in hash_lst, 'test fail, RSS hash is same.')

        # destroy rule to test
        self.pmd_output.execute_cmd("flow destroy 1 rule 0")
        self.pmd_output.execute_cmd("flow destroy 1 rule 1")
        self.pmd_output.execute_cmd("flow list 1")
        self.pmd_output.execute_cmd("flow destroy 2 rule 0")
        self.pmd_output.execute_cmd("flow destroy 2 rule 1")
        self.pmd_output.execute_cmd("flow list 2")
        out_data = {}
        for dst_mac in dst_mac_lst:
            pkt_lst = [pkt.format(dst_mac) for pkt in module_pkt_lst]
            reta_line = self.get_receive_lst(tag_lst[:1], pkt_lst, stats=False)
            out_data.setdefault(dst_mac, reta_line)
        # verify
        for key in out_data.keys():
            hash_lst = [i.get('RSS hash') for i in out_data[key]]
            self.verify(len(set(hash_lst)) == 1, 'test fail, RSS hash is same.')

    def test_rss_without_or_with_udp_port_set_for_udp_ecpri_rule(self):
        tag_lst = ['x45', 'x46', 'x47', 'x48']
        pkt = "Ether(dst='{}')/IP()/UDP(dport=0x5123)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')".format(Mac_list[1])
        self.pmd_output.execute_cmd("flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end "
                               "actions rss types ecpri end key_len 0 queues end / end")
        out_data = self.get_receive_lst(tag_lst, [pkt])
        # verify
        hash_lst = [i.get('RSS hash') for i in out_data]
        self.verify(len(set(hash_lst)) == 1, 'test fail, rule worked!')
        # set ecpri and test
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri 0x5123")
        out_data = self.get_receive_lst(tag_lst[:2], [pkt])
        # verify
        hash_lst = [i.get('RSS hash') for i in out_data]
        self.verify(len(set(hash_lst)) == 2 and None not in hash_lst, 'test fail, rule not worked!')

    def test_DCF_reset_for_udp_ecpri_rss(self):
        tag_lst = ['x45', 'x46', 'x47']
        pkt = "Ether(dst='{}')/IP()/UDP(dport=0x5123)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')".format(Mac_list[1])
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri 0x5123")
        self.pmd_output.execute_cmd("flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end "
                               "actions rss types ecpri end key_len 0 queues end / end")
        out_data = self.get_receive_lst(tag_lst[:2], [pkt])
        # verify
        hash_lst = [i.get('RSS hash') for i in out_data]
        self.verify(len(set(hash_lst)) == 2 and None not in hash_lst, 'test fail, RSS hash is same')

        self.new_session.send_expect("ip link set {} vf 0 mac 00:11:22:33:44:66".format(self.pf_interface), "#")
        out_data = self.get_receive_lst(tag_lst, [pkt])
        # verify
        hash_lst = [i.get('RSS hash') for i in out_data]
        self.verify(len(set(hash_lst)) == 1, 'test fail, RSS hash is not same')

        # restart testpmd and test
        new_mac = "00:11:22:33:44:55"
        self.new_session.send_expect("ip link set {} vf 0 mac {}".format(self.pf_interface, new_mac), "#")
        self.dut.send_expect("quit", "# ")
        self.launch_testpmd()
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri 0x5123")
        self.pmd_output.execute_cmd("flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end "
                               "actions rss types ecpri end key_len 0 queues end / end")
        out_data = self.get_receive_lst(tag_lst[:2], [pkt])
        # verify
        hash_lst = [i.get('RSS hash') for i in out_data]
        self.verify(len(set(hash_lst)) == 2 and None not in hash_lst, 'test fail, RSS hash is same')

        self.new_session.send_expect("ip link set {} vf 0 mac 00:11:22:33:44:66".format(self.pf_interface), "#")
        out_data = self.get_receive_lst(tag_lst, [pkt])
        # verify
        hash_lst = [i.get('RSS hash') for i in out_data]
        self.verify(len(set(hash_lst)) == 1, 'test fail, RSS hash is not same')

        self.dut.send_expect("quit", "# ")
        self.launch_testpmd()
        self.new_session.send_expect("ip link set {} vf 0 trust off".format(self.pf_interface), "#")
        out_data = self.get_receive_lst(tag_lst, [pkt])
        # verify
        hash_lst = [i.get('RSS hash') for i in out_data]
        self.verify(len(set(hash_lst)) == 1, 'test fail, RSS hash is not same')

    def test_DCF_reset_for_eth_ecpri_rss(self):
        tag_lst = ['x45', 'x46', 'x47', 'x48']
        pkt = "Ether(dst='{}', type=0xAEFE)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')"
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri 0x5123")
        self.pmd_output.execute_cmd("flow create 1 ingress pattern eth / ecpri common type iq_data / end actions rss types"
                                    " ecpri end key_len 0 queues end / end")

        out_data = self.get_receive_lst(tag_lst[:2], [pkt])
        # verify
        hash_lst = [i.get('RSS hash') for i in out_data]
        self.verify(len(set(hash_lst)) == 2 and None not in hash_lst, 'test fail, RSS hash is same')
        self.new_session.send_expect("ip link set {} vf 0 mac 00:11:22:33:44:66".format(self.pf_interface), "#")
        out_data = self.get_receive_lst(tag_lst[1:], [pkt])
        # verify
        hash_lst = [i.get('RSS hash') for i in out_data]
        self.verify(len(set(hash_lst)) == 3 and None not in hash_lst, 'test fail, RSS hash is same')

        self.new_session.send_expect("ip link set {} vf 0 trust off".format(self.pf_interface), "#")
        out_data = self.get_receive_lst(tag_lst[:2], [pkt])
        # verify
        hash_lst = [i.get('RSS hash') for i in out_data]
        self.verify(len(set(hash_lst)) == 2 and None not in hash_lst, 'test fail, RSS hash is same')

        self.new_session.send_expect("ip link set {} vf 0 mac 00:11:22:33:44:66".format(self.pf_interface), "#")
        out_data = self.get_receive_lst(tag_lst[1:], [pkt])
        # verify
        hash_lst = [i.get('RSS hash') for i in out_data]
        self.verify(len(set(hash_lst)) == 3 and None not in hash_lst, 'test fail, RSS hash is same')

    def test_DCF_exit_for_eth_ecpri_and_udp_ecpri_rss(self):
        self.dut.send_expect("quit", "# ")
        eal_param = " -a {},cap=dcf".format(self.sriov_vfs_port[0].pci)
        self.pmd_output.start_testpmd(cores=list(range(8)), eal_param=eal_param, prefix="test1", socket=self.ports_socket)
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri 0x5123")
        pmd_output1 = PmdOutput(self.dut, self.new_session)
        eal_param1 = " -a {} -a {}".format(self.sriov_vfs_port[1].pci, self.sriov_vfs_port[2].pci)
        param = " --rxq=16 --txq=16"
        pmd_output1.start_testpmd(cores=list(range(8)), eal_param=eal_param1, param=param, prefix="test2",
                                  socket=self.ports_socket)
        pmd_output1.execute_cmd("flow create 0 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end "
                                "actions rss types ecpri end key_len 0 queues end / end")
        pmd_output1.execute_cmd("flow create 1 ingress pattern eth / ecpri common type iq_data / end actions rss "
                                "types ecpri end key_len 0 queues end / end")
        pmd_output1.execute_cmd("set verbose 1")
        pmd_output1.execute_cmd("set fwd rxonly")
        pmd_output1.execute_cmd("start")
        tag_lst = ['x45', 'x46']
        pkt_lst = ["Ether(dst='{}')/IP()/UDP(dport=0x5123)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s')".format(Mac_list[1]),
                   "Ether(dst='{}', type=0xAEFE)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')".format(Mac_list[2])
                   ]
        out_data = self.get_receive_lst(tag_lst, pkt_lst, pmd_output1)
        # verify
        hash_lst = [i.get('RSS hash') for i in out_data]
        self.verify(len(set(hash_lst)) == 4 and None not in hash_lst, 'test fail, Rss hash is same.')
        self.pmd_output.execute_cmd("quit", "#")
        out_data = self.get_receive_lst(tag_lst, pkt_lst, pmd_output1)
        # verify
        hash_lst = [i.get('RSS hash') for i in out_data]
        self.verify(hash_lst[0] == hash_lst[2] and hash_lst[1] != hash_lst[3], 'test fail, hash value is wrong.')
        pmd_output1.execute_cmd("quit", '#')

    def create_fdir_rule(self, rule: (list, str), check_stats=None, msg=None, validate=True):
        if validate:
            if isinstance(rule, list):
                validate_rule = [i.replace('create', 'validate') for i in rule]
            else:
                validate_rule = rule.replace('create', 'validate')
            self.validate_fdir_rule(validate_rule, check_stats=check_stats)
        p = re.compile(r"Flow rule #(\d+) created")
        rule_list = []
        if isinstance(rule, list):
            for i in rule:
                out = self.pmd_output.execute_cmd(i, timeout=1)
                if msg:
                    self.verify(msg in out, "failed: expect %s in %s" % (msg, out))
                m = p.search(out)
                if m:
                    rule_list.append(m.group(1))
                else:
                    rule_list.append(False)
        elif isinstance(rule, str):
            out = self.pmd_output.execute_cmd(rule, timeout=1)
            if msg:
                self.verify(msg in out, "failed: expect %s in %s" % (msg, out))
            m = p.search(out)
            if m:
                rule_list.append(m.group(1))
            else:
                rule_list.append(False)
        else:
            raise Exception("unsupported rule type, only accept list or str")
        if check_stats:
            self.verify(all(rule_list), "some rules create failed, result %s" % rule_list)
        elif check_stats == False:
            self.verify(not any(rule_list), "all rules should create failed, result %s" % rule_list)
        return rule_list

    def validate_fdir_rule(self, rule, check_stats=True, check_msg=None):
        flag = 'Flow rule validated'
        if isinstance(rule, str):
            out = self.pmd_output.execute_cmd(rule, timeout=1)
            if check_stats:
                self.verify(flag in out.strip(), "rule %s validated failed, result %s" % (rule, out))
            else:
                if check_msg:
                    self.verify(flag not in out.strip() and check_msg in out.strip(),
                                "rule %s validate should failed with msg: %s, but result %s" % (rule, check_msg, out))
                else:
                    self.verify(flag not in out.strip(), "rule %s validate should failed, result %s" % (rule, out))
        elif isinstance(rule, list):
            for r in rule:
                out = self.pmd_output.execute_cmd(r, timeout=1)
                if check_stats:
                    self.verify(flag in out.strip(), "rule %s validated failed, result %s" % (r, out))
                else:
                    if not check_msg:
                        self.verify(flag not in out.strip(), "rule %s validate should failed, result %s" % (r, out))
                    else:
                        self.verify(flag not in out.strip() and check_msg in out.strip(),
                                    "rule %s should validate failed with msg: %s, but result %s" % (
                                        r, check_msg, out))

    def check_fdir_rule(self, port_id=0, stats=True, rule_list=None):
        out = self.pmd_output.execute_cmd("flow list %s" % port_id)
        p = re.compile(r"ID\s+Group\s+Prio\s+Attr\s+Rule")
        matched = p.search(out)
        if stats:
            self.verify(matched, "flow rule on port %s is not existed" % port_id)
            if rule_list:
                p = re.compile("^(\d+)\s")
                li = out.splitlines()
                res = list(filter(bool, list(map(p.match, li))))
                result = [i.group(1) for i in res]
                self.verify(sorted(result) == sorted(rule_list),
                            "check rule list failed. expect %s, result %s" % (rule_list, result))
        else:
            if rule_list:
                p = re.compile("^(\d+)\s")
                li = out.splitlines()
                res = list(filter(bool, list(map(p.match, li))))
                result = [i.group(1) for i in res]
                self.verify(not [i for i in rule_list if i in result],
                            "check rule list failed. flow rule %s on port %s is existed" % (rule_list, port_id))
            else:
                self.verify(not matched, "flow rule on port %s is existed" % port_id)

    def destroy_fdir_rule(self, port_id=0, rule_id=None):
        if rule_id is None:
            rule_id = 0
        if isinstance(rule_id, list):
            for i in rule_id:
                out = self.dut.send_command("flow destroy %s rule %s" % (port_id, i), timeout=1)
                p = re.compile(r"Flow rule #(\d+) destroyed")
                m = p.search(out)
                self.verify(m, "flow rule %s delete failed" % rule_id)
        else:
            out = self.dut.send_command("flow destroy %s rule %s" % (port_id, rule_id), timeout=1)
            p = re.compile(r"Flow rule #(\d+) destroyed")
            m = p.search(out)
            self.verify(m, "flow rule %s delete failed" % rule_id)

    def send_packets(self, packets, tx_port=None, count=1):
        self.pkt.update_pkt(packets)
        tx_port = self.tester_iface0 if not tx_port else tx_port
        self.pkt.send_pkt(crb=self.tester, tx_port=tx_port, count=count)

    def send_pkts_getouput(self, pkts, port_id=0, count=1, drop=False):
        tx_port = self.tester_iface0 if port_id == 0 else self.tester_iface1

        time.sleep(1)
        if drop:
            self.pmd_output.execute_cmd("clear port stats all")
            time.sleep(0.5)
            self.send_packets(pkts, tx_port=tx_port, count=count)
            out = self.pmd_output.execute_cmd("stop")
            self.pmd_output.execute_cmd("start")
        else:
            self.send_packets(pkts, tx_port=tx_port, count=count)
            out = self.pmd_output.get_output()
        return out

    def _rte_flow_validate(self, vectors):
        test_results = {}
        for tv in vectors:
            try:
                count = 1
                port_id = tv["send_port"]["port_id"] if tv["send_port"].get("port_id") is not None else 0
                dut_port_id = tv["check_param"]["port_id"] if tv["check_param"].get("port_id") is not None else 0
                drop = tv["check_param"].get("drop")
                # create rule
                rule_li = self.create_fdir_rule(tv["rule"], check_stats=True)
                # send and check match packets
                out1 = self.send_pkts_getouput(pkts=tv["scapy_str"]["match"], port_id=port_id,
                                               count=count, drop=drop)
                matched_queue = tv["check_func"](out1, pkt_num=len(tv["scapy_str"]["match"]),
                                                 check_param=tv["check_param"])
                # send and check unmatched packets
                out2 = self.send_pkts_getouput(pkts=tv["scapy_str"]["unmatched"], port_id=port_id,
                                               count=count, drop=drop)
                tv["check_func"](out2, pkt_num=len(tv["scapy_str"]["unmatched"]), check_param=tv["check_param"],
                                 stats=False)
                # list and destroy rule
                self.check_fdir_rule(port_id=tv["check_param"]["port_id"], rule_list=['0'] + rule_li)
                self.destroy_fdir_rule(rule_id=rule_li, port_id=dut_port_id)
                # send matched packet
                out3 = self.send_pkts_getouput(pkts=tv["scapy_str"]["match"], port_id=port_id,
                                               count=count, drop=drop)
                matched_queue2 = tv["check_func"](out3, pkt_num=len(tv["scapy_str"]["match"]),
                                                  check_param=tv["check_param"],
                                                  stats=False)
                if tv["check_param"].get("rss"):
                    self.verify(matched_queue == matched_queue2 and None not in matched_queue,
                                "send twice matched packet, received in deferent queues")
                # check not rule exists
                self.check_fdir_rule(port_id=dut_port_id, rule_list=rule_li, stats=False)
                test_results[tv["name"]] = True
                self.logger.info((GREEN("case passed: %s" % tv["name"])))
            except Exception as e:
                self.logger.warning((RED(e)))
                self.dut.send_command("flow flush 0", timeout=1)
                self.dut.send_command("flow flush 1", timeout=1)
                test_results[tv["name"]] = False
                self.logger.info((GREEN("case failed: %s" % tv["name"])))
                continue
        failed_cases = []
        for k, v in list(test_results.items()):
            if not v:
                failed_cases.append(k)
        self.verify(all(test_results.values()), "{} failed.".format(failed_cases))

    def test_eCPRI_over_Ethernet_header_pattern_fdir(self):
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri 0x5123")
        self.create_fdir_rule(rule=eCPRI_over_Ethernet_rule, check_stats=True)
        self._rte_flow_validate(tv_over_eth)

    def test_eCPRI_over_IP_or_UDP_header_pattern_fdir(self):
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri 0x5123")
        self.create_fdir_rule(rule=eCPRI_over_IP_UDP_rule, check_stats=True)
        self._rte_flow_validate(tv_over_ip_udp)

    def test_ecpri_fdir_multirules(self):
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri 0x5123")
        rule_lst = ["flow create 1 ingress pattern eth / ecpri common type iq_data / end actions rss types ecpri end "
                    "key_len 0 queues end / end",
                    "flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end actions rss "
                    "types ecpri end key_len 0 queues end / end",
                    "flow create 2 ingress pattern eth / ecpri common type iq_data / end actions rss types ecpri end "
                    "key_len 0 queues end / end",
                    "flow create 2 ingress pattern eth / ipv4 / udp / ecpri common type iq_data / end actions rss "
                    "types ecpri end key_len 0 queues end / end",
                    "flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2345 / end "
                    "actions rss queues 5 6 end / mark id 0 / end",
                    "flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2346 / end "
                    "actions passthru / mark id 1 / end",
                    "flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end actions "
                    "drop / end",
                    "flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is 0x2346 / end actions "
                    "queue index 1 / mark id 2 / end",
                    "flow create 2 ingress pattern eth / ecpri common type iq_data pc_id is 0x2346 / end actions "
                    "mark id 3 / end",
                    "flow create 2 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is 0x2346 / end "
                    "actions mark / rss / end"]
        for rule in rule_lst:
            self.pmd_output.execute_cmd(rule)
        tag_lst = ['x45', 'x46']
        module_pkt_lst = ["Ether(dst='{}')/IP()/UDP(dport=0x5123)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')",
                          "Ether(dst='{}', type=0xAEFE)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')"]
        pkt_lst = ["Ether(dst='{}')/IP()/UDP(dport=0x5123)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')".format(Mac_list[1])]
        data_lst = self.get_receive_lst(tag_lst[: 1], pkt_lst, stats=False)
        queue = [data.get('queue') for data in data_lst]
        self.verify([i for i in queue if i in ['5', '6']], 'pkt go to wrong queue!')
        self.verify([data.get('FDIR matched ID') for data in data_lst] == ['0x0'], 'pkt has wrong mark id!')
        data_lst = self.get_receive_lst(tag_lst[1: ], pkt_lst)
        self.verify([data.get('FDIR matched ID') for data in data_lst] == ['0x1'], 'pkt has wrong mark id!')
        pkt_lst = ["Ether(dst='{}', type=0xAEFE)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')".format(Mac_list[1])]
        data_lst = self.get_receive_lst(tag_lst, pkt_lst, stats=False)
        self.verify([data.get('queue') for data in data_lst] == [None, '1'], 'pkt go to wrong queue!')
        self.verify([data.get('FDIR matched ID') for data in data_lst] == [None, '0x2'], 'pkt has wrong mark id!')
        pkt_lst = [pkt.format(Mac_list[2]) for pkt in module_pkt_lst]
        data_lst = self.get_receive_lst(tag_lst, pkt_lst)
        self.verify([data.get('FDIR matched ID') for data in data_lst] == [None, None, '0x0', '0x3'], 'pkt has wrong mark id!')

    def test_ecpri_fdir_negative_case(self):
        out = self.pmd_output.execute_cmd("flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id is "
                               "0x2345 / end actions rss queues 5 6 end / mark id 0 / end")
        self.verify("Failed to create parser engine.: Invalid argument" in out, "test fail, bad rule set success.")
        out = self.pmd_output.execute_cmd("flow list 1")
        r = r'flow list 1(\s+)(.*)'
        m = re.match(r, out)
        self.verify(m.group(2) == '', 'bad rule set successful!')

    def test_ecpri_fdir_when_DCF_reset(self):
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri 0x5123")
        self.pmd_output.execute_cmd("flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id "
                                    "is 0x2345 / end actions queue index 1 / mark id 1 / end")
        self.pmd_output.execute_cmd("flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is "
                                    "0x2345 / end actions queue index 2 / mark id 2 / end")
        pkt_lst = ["Ether(dst='{}')/IP()/UDP(dport=0x5123)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')".format(Mac_list[1]),
                   "Ether(dst='{}', type=0xAEFE)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')".format(Mac_list[1])]
        tag_lst = ['x45']
        data_lst = self.get_receive_lst(tag_lst, pkt_lst)
        # verify
        self.verify([data.get('queue') for data in data_lst] == ['1', '2'], "pkt to the wrong queue!")
        self.verify([data.get('FDIR matched ID') for data in data_lst] == ['0x1', '0x2'], "pkt with wrong FDIR matched ID!")
        self.new_session.send_expect('ip link set {} vf 0 mac 00:11:22:33:44:66'.format(self.pf_interface), '#')
        data_lst = self.get_receive_lst(tag_lst, pkt_lst)
        # verify
        self.verify(data_lst[1].get('queue') == '2', "pkt to the wrong queue!")
        self.verify([data.get('FDIR matched ID') for data in data_lst] == [None, '0x2'], "pkt with wrong FDIR matched ID!")
        self.dut.send_expect("quit", "#")
        self.launch_testpmd()
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri 0x5123")
        self.pmd_output.execute_cmd("flow create 1 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id "
                                    "is 0x2345 / end actions queue index 1 / mark id 1 / end")
        self.pmd_output.execute_cmd("flow create 1 ingress pattern eth / ecpri common type iq_data pc_id is "
                                    "0x2345 / end actions queue index 2 / mark id 2 / end")
        data_lst = self.get_receive_lst(tag_lst, pkt_lst)
        self.verify([data.get('queue') for data in data_lst] == ['1', '2'], "pkt to the wrong queue!")
        self.verify([data.get('FDIR matched ID') for data in data_lst] == ['0x1', '0x2'], "pkt with wrong FDIR matched ID!")
        self.new_session.send_expect("ip link set {} vf 0 trust off".format(self.pf_interface), "#")
        data_lst = self.get_receive_lst(tag_lst, pkt_lst)
        self.verify(data_lst[1].get('queue') == '2', "pkt to the wrong queue!")
        self.verify([data.get('FDIR matched ID') for data in data_lst] == [None, '0x2'], "pkt with wrong FDIR matched ID!")

    def test_ecpri_fdir_when_DCF_exit(self):
        self.dut.send_expect("quit", "#")
        eal_param = " -a {},cap=dcf".format(self.sriov_vfs_port[0].pci)
        self.pmd_output.start_testpmd(cores=list(range(8)), eal_param=eal_param, prefix="test1",
                                      socket=self.ports_socket)
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add ecpri 0x5123")
        pmd_output1 = PmdOutput(self.dut, self.new_session)
        eal_param1 = " -a {} -a {}".format(self.sriov_vfs_port[1].pci, self.sriov_vfs_port[2].pci)
        param = " --rxq=16 --txq=16"
        pmd_output1.start_testpmd(cores=list(range(8)), eal_param=eal_param1, param=param, prefix="test2",
                                  socket=self.ports_socket)
        pmd_output1.execute_cmd("flow create 0 ingress pattern eth / ipv4 / udp / ecpri common type iq_data pc_id "
                                "is 0x2345 / end actions queue index 1 / mark id 1 / end")
        pmd_output1.execute_cmd("flow create 0 ingress pattern eth / ecpri common type iq_data pc_id is 0x2345 / end "
                                "actions queue index 2 / mark id 2 / end")
        pmd_output1.execute_cmd("set verbose 1")
        pmd_output1.execute_cmd("set fwd rxonly")
        pmd_output1.execute_cmd("start")
        pkt_lst = ["Ether(dst='{}')/IP()/UDP(dport=0x5123)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')".format(Mac_list[1]),
                   "Ether(dst='{}', type=0xAEFE)/Raw(\'\\x10\\x00\\x02\\x24\\x23\\%s\')".format(Mac_list[1])]
        tag_lst = ['x45']
        data_lst = self.get_receive_lst(tag_lst, pkt_lst, pmd_output=pmd_output1)
        # verify
        self.verify([data.get('FDIR matched ID') for data in data_lst] == ['0x1', '0x2'] and [data.get('queue') for data in data_lst] == ['1', '2'], 'mark id or queue wrong!')

        self.dut.send_expect("quit", "#")
        data_lst = self.get_receive_lst(tag_lst, pkt_lst, pmd_output=pmd_output1)
        # verify
        self.verify([data.get('FDIR matched ID') for data in data_lst] == [None, '0x2'] and data_lst[1].get('queue') == '2', 'mark id or queue wrong!')

    def get_receive_lst(self, tag_lst=[], pkt_lst=[], pmd_output='', stats=True):
        data_lst = []
        for tag in tag_lst:
            for pkt in pkt_lst:
                pkt_str = pkt % tag
                out = self.send_pkt(pkt_str=pkt_str, pmd_output=pmd_output)
                rfc.verify_directed_by_rss(out, rxq=16, stats=stats)
                reta_line = self.get_receive_data(out)
                data_lst.append(reta_line)
        return data_lst

    def get_receive_data(self, out):
        reta_line = {}
        lines = out.split("\r\n")
        for line in lines:
            line = line.strip()
            if len(line) != 0 and line.strip().startswith("port "):
                reta_line = {}
                rexp = r"port (\d)/queue (\d{1,2}): received (\d) packets"
                m = re.match(rexp, line.strip())
                if m:
                    reta_line["port"] = m.group(1)
                    reta_line["queue"] = m.group(2)

            elif len(line) != 0 and line.startswith(("src=",)):
                for item in line.split("-"):
                    item = item.strip()
                    if item.startswith("RSS hash"):
                        name, value = item.split("=", 1)
                        reta_line[name.strip()] = value.strip()
                    elif item.startswith("FDIR matched ID"):
                        name, value = item.split("=", 1)
                        reta_line[name.strip()] = value.strip()
        return reta_line

    def compile_dpdk(self):
        cmd_lst = [r"sed -i '/iavf_flex_rxd_to_vlan_tci(rxm, &rxd, rxq->rx_flags);/i\printf(\"++++++++++++ptype=%u\\n\",IAVF_RX_FLEX_DESC_PTYPE_M & rte_le_to_cpu_16(rxd.wb.ptype_flex_flags0));' ",
                   r"sed -i '/IAVF_DEV_PRIVATE_TO_VF(dev->data->dev_private);/{:a;n;s/ifdef RTE_ARCH_X86/if 0/g;/struct iavf_rx_queue/!ba}' ",
                   r"sed -i '/rx_pkt_burst = iavf_recv_pkts;/{n;s/\}/\}dev->rx_pkt_burst = iavf_recv_pkts_flex_rxd;\n/g}' "]
        for cmd in cmd_lst:
            self.dut.send_expect(cmd + self.file_path, "#")
        self.dut.build_install_dpdk(self.target)

    def send_and_verify(self, dts_mac, ecpri, if_match=True):
        ptype_lst = ptype_match_lst if if_match else ptype_nomatch_lst
        for i in range(len(pkt_lst)):
            out = self.send_pkt(pkt_lst[i], dts_mac=dts_mac, ecpri=ecpri)
            self.verify(ptype_lst[i] in out, 'ptype is error, expect {}'.format(ptype_lst[i]))

    def send_pkt(self, pkt_str='', dts_mac='00:11:22:33:44:11', ecpri='0x5123', pmd_output=''):
        self.pkt.append_pkt(pkt_str.format(dts_mac, ecpri))
        self.pkt.send_pkt(crb=self.tester, tx_port=self.tester_iface0, count=1)
        out = pmd_output.get_output() if pmd_output else self.pmd_output.get_output()
        self.pkt.update_pkt([])
        return out

    def tear_down(self):
        self.dut.kill_all()

    def tear_down_all(self):
        self.new_session.close()
        self.dut.kill_all()
