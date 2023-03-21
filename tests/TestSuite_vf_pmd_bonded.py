# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2023 Intel Corporation
#

"""
DPDK Test suite.


Test userland 10Gb PMD.

"""

import random
import re
import time
from socket import htonl, htons

import framework.utils as utils
import tests.bonding as bonding
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

SOCKET_0 = 0
SOCKET_1 = 1

MODE_ROUND_ROBIN = "ROUND_ROBIN(0)"
MODE_ACTIVE_BACKUP = "ACTIVE_BACKUP(1)"
MODE_XOR_BALANCE = "BALANCE(2)"
MODE_BROADCAST = "BROADCAST(3)"
MODE_LACP = "8023AD(4)"
MODE_TLB_BALANCE = "TLB(5)"
MODE_ALB_BALANCE = "ALB(6)"

FRAME_SIZE_64 = 64
FRAME_SIZE_65 = 65
FRAME_SIZE_128 = 128
FRAME_SIZE_256 = 256
FRAME_SIZE_512 = 512
FRAME_SIZE_1024 = 1024
FRAME_SIZE_1280 = 1280
FRAME_SIZE_1518 = 1518

S_MAC_IP_PORT = [
    ("52:00:00:00:00:00", "10.239.129.65", 61),
    ("52:00:00:00:00:01", "10.239.129.66", 62),
    ("52:00:00:00:00:02", "10.239.129.67", 63),
]

D_MAC_IP_PORT = []
LACP_MESSAGE_SIZE = 128


class TestVFPmdBonded(TestCase):
    def get_stats(self, portid, rx_tx):
        """
        Get packets number from port statistic
        """

        out = self.dut.send_expect("show port stats %d" % portid, "testpmd> ")

        if rx_tx == "rx":
            result_scanner = (
                r"RX-packets: ([0-9]+)\s*RX-missed: ([0-9]+)\s*RX-bytes:  ([0-9]+)"
            )
        elif rx_tx == "tx":
            result_scanner = (
                r"TX-packets: ([0-9]+)\s*TX-errors: ([0-9]+)\s*TX-bytes:  ([0-9]+)"
            )
        else:
            return None

        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.search(out)

        return m.groups()

    def parse_ether_ip(self, dest_port, **ether_ip):
        """
        ether_ip:
            'ether':
                {
                    'dest_mac':False
                    'src_mac':"52:00:00:00:00:00"
                }
            'dot1q':
                {
                    'vlan':1
                }
            'ip':
                {
                    'dest_ip':"10.239.129.88"
                    'src_ip':"10.239.129.65"
                }
            'udp':
                {
                    'dest_port':53
                    'src_port':53
                }
        """
        ret_ether_ip = {}
        ether = {}
        dot1q = {}
        ip = {}
        udp = {}
        try:
            dut_dest_port = self.vf_ports[dest_port]
        except Exception as e:
            dut_dest_port = dest_port

        query_type = "mac"
        if not ether_ip.get("ether"):
            ether["dest_mac"] = self.bond_inst.get_port_mac(dut_dest_port, query_type)
            ether["src_mac"] = "52:00:00:00:00:00"
        else:
            if not ether_ip["ether"].get("dest_mac"):
                ether["dest_mac"] = self.bond_inst.get_port_mac(
                    dut_dest_port, query_type
                )
            else:
                ether["dest_mac"] = ether_ip["ether"]["dest_mac"]
            if not ether_ip["ether"].get("src_mac"):
                ether["src_mac"] = "52:00:00:00:00:00"
            else:
                ether["src_mac"] = ether_ip["ether"]["src_mac"]

        if not ether_ip.get("dot1q"):
            pass
        else:
            if not ether_ip["dot1q"].get("vlan"):
                dot1q["vlan"] = "1"
            else:
                dot1q["vlan"] = ether_ip["dot1q"]["vlan"]

        if not ether_ip.get("ip"):
            ip["dest_ip"] = "10.239.129.88"
            ip["src_ip"] = "10.239.129.65"
        else:
            if not ether_ip["ip"].get("dest_ip"):
                ip["dest_ip"] = "10.239.129.88"
            else:
                ip["dest_ip"] = ether_ip["ip"]["dest_ip"]
            if not ether_ip["ip"].get("src_ip"):
                ip["src_ip"] = "10.239.129.65"
            else:
                ip["src_ip"] = ether_ip["ip"]["src_ip"]

        if not ether_ip.get("udp"):
            udp["dest_port"] = 53
            udp["src_port"] = 53
        else:
            if not ether_ip["udp"].get("dest_port"):
                udp["dest_port"] = 53
            else:
                udp["dest_port"] = ether_ip["udp"]["dest_port"]
            if not ether_ip["udp"].get("src_port"):
                udp["src_port"] = 53
            else:
                udp["src_port"] = ether_ip["udp"]["src_port"]

        ret_ether_ip["ether"] = ether
        ret_ether_ip["dot1q"] = dot1q
        ret_ether_ip["ip"] = ip
        ret_ether_ip["udp"] = udp

        return ret_ether_ip

    def send_packet(
        self,
        dest_port,
        src_port=False,
        frame_size=FRAME_SIZE_64,
        count=1,
        invert_verify=False,
        **ether_ip,
    ):
        """
        Send count packet to portid
        count: 1 or 2 or 3 or ... or 'MANY'
               if count is 'MANY', then set count=100000,
               send packets during 5 seconds.
        ether_ip:
            'ether':
                {
                    'dest_mac':False
                    'src_mac':"52:00:00:00:00:00"
                }
            'dot1q':
                {
                    'vlan':1
                }
            'ip':
                {
                    'dest_ip':"10.239.129.88"
                    'src_ip':"10.239.129.65"
                }
            'udp':
                {
                    'dest_port':53
                    'src_port':53
                }
        """
        during = 0
        loop = 0
        try:
            count = int(count)
        except ValueError as e:
            if count == "MANY":
                during = 5
                count = 100000
            else:
                raise e

        if not src_port:
            gp0rx_pkts, gp0rx_err, gp0rx_bytes = [
                int(_) for _ in self.get_stats(self.vf_ports[dest_port], "rx")
            ]
            itf = self.tester.get_interface(
                self.tester.get_local_port(self.dut_ports[dest_port])
            )
        else:
            gp0rx_pkts, gp0rx_err, gp0rx_bytes = [
                int(_) for _ in self.get_stats(dest_port, "rx")
            ]
            itf = src_port

        ret_ether_ip = self.parse_ether_ip(dest_port, **ether_ip)

        pktlen = frame_size - 18
        padding = pktlen - 20

        start = time.time()
        while True:
            self.tester.scapy_foreground()
            self.tester.scapy_append('nutmac="%s"' % ret_ether_ip["ether"]["dest_mac"])
            self.tester.scapy_append('srcmac="%s"' % ret_ether_ip["ether"]["src_mac"])

            if ether_ip.get("dot1q"):
                self.tester.scapy_append("vlanvalue=%d" % ret_ether_ip["dot1q"]["vlan"])
            self.tester.scapy_append('destip="%s"' % ret_ether_ip["ip"]["dest_ip"])
            self.tester.scapy_append('srcip="%s"' % ret_ether_ip["ip"]["src_ip"])
            self.tester.scapy_append("destport=%d" % ret_ether_ip["udp"]["dest_port"])
            self.tester.scapy_append("srcport=%d" % ret_ether_ip["udp"]["src_port"])
            if not ret_ether_ip.get("dot1q"):
                pkt = (
                    'sendp([Ether(dst=nutmac, src=srcmac)/IP(dst=destip, src=srcip, len=%s)/\
UDP(sport=srcport, dport=destport)/Raw(load="\x50"*%s)], iface="%s", count=%d, verbose=False)'
                    % (pktlen, padding, itf, count)
                )
                self.tester.scapy_append(pkt)
            else:
                pkt = (
                    'sendp([Ether(dst=nutmac, src=srcmac)/Dot1Q(vlan=vlanvalue)/IP(dst=destip, src=srcip, len=%s)/\
UDP(sport=srcport, dport=destport)/Raw(load="\x50"*%s)], iface="%s", count=%d, verbose=False)'
                    % (pktlen, padding, itf, count)
                )
                self.tester.scapy_append(pkt)
            self.tester.scapy_execute(timeout=180)
            loop += 1

            now = time.time()
            if (now - start) >= during:
                break
        time.sleep(0.5)

        if not src_port:
            p0rx_pkts, p0rx_err, p0rx_bytes = [
                int(_) for _ in self.get_stats(self.vf_ports[dest_port], "rx")
            ]
        else:
            p0rx_pkts, p0rx_err, p0rx_bytes = [
                int(_) for _ in self.get_stats(dest_port, "rx")
            ]

        p0rx_pkts -= gp0rx_pkts
        p0rx_bytes -= gp0rx_bytes

        if not invert_verify:
            self.verify(p0rx_pkts >= count * loop, "Data not received by port")
        else:
            global LACP_MESSAGE_SIZE
            self.verify(
                p0rx_pkts == 0 or p0rx_bytes / p0rx_pkts == LACP_MESSAGE_SIZE,
                "Data received by port, but should not.",
            )
        return count * loop

    def get_value_from_str(self, key_str, regx_str, string):
        """
        Get some values from the given string by the regular expression.
        """
        pattern = r"(?<=%s)%s" % (key_str, regx_str)
        s = re.compile(pattern)
        res = s.search(string)
        if type(res).__name__ == "NoneType":
            return " "
        else:
            return res.group(0)

    def get_detail_from_port_info(self, key_str, regx_str, port):
        """
        Get the detail info from the output of pmd cmd 'show port info <port num>'.
        """
        out = self.dut.send_expect("show port info %d" % port, "testpmd> ")
        find_value = self.get_value_from_str(key_str, regx_str, out)
        return find_value

    def get_port_mac(self, port_id):
        """
        Get the specified port MAC.
        """
        return self.get_detail_from_port_info(
            "MAC address: ", "([0-9A-F]{2}:){5}[0-9A-F]{2}", port_id
        )

    def get_port_connect_socket(self, port_id):
        """
        Get the socket id which the specified port is connecting with.
        """
        return self.get_detail_from_port_info("Connect to socket: ", "\d+", port_id)

    def get_port_memory_socket(self, port_id):
        """
        Get the socket id which the specified port memory is allocated on.
        """
        return self.get_detail_from_port_info(
            "memory allocation on the socket: ", "\d+", port_id
        )

    def get_port_link_status(self, port_id):
        """
        Get the specified port link status now.
        """
        return self.get_detail_from_port_info("Link status: ", "\d+", port_id)

    def get_port_link_speed(self, port_id):
        """
        Get the specified port link speed now.
        """
        return self.get_detail_from_port_info("Link speed: ", "\d+", port_id)

    def get_port_link_duplex(self, port_id):
        """
        Get the specified port link mode, duplex or simplex.
        """
        return self.get_detail_from_port_info("Link duplex: ", "\S+", port_id)

    def get_port_promiscuous_mode(self, port_id):
        """
        Get the promiscuous mode of port.
        """
        return self.get_detail_from_port_info("Promiscuous mode: ", "\S+", port_id)

    def get_port_allmulticast_mode(self, port_id):
        """
        Get the allmulticast mode of port.
        """
        return self.get_detail_from_port_info("Allmulticast mode: ", "\S+", port_id)

    def get_port_vlan_offload(self, port_id):
        """
        Function: get the port vlan setting info.
        return value:
            'strip':'on'
            'filter':'on'
            'qinq':'off'
        """
        vlan_info = {}
        vlan_info["strip"] = self.get_detail_from_port_info("strip ", "\S+", port_id)
        vlan_info["filter"] = self.get_detail_from_port_info("filter", "\S+", port_id)
        vlan_info["qinq"] = self.get_detail_from_port_info(
            "qinq\(extend\) ", "\S+", port_id
        )
        return vlan_info

    def get_info_from_bond_config(self, key_str, regx_str, bond_port):
        """
        Get info by executing the command "show bonding config".
        """
        out = self.dut.send_expect("show bonding config %d" % bond_port, "testpmd> ")
        find_value = self.get_value_from_str(key_str, regx_str, out)
        return find_value

    def get_bond_mode(self, bond_port):
        """
        Get the  mode of the bonding device  which you choose.
        """
        return self.get_info_from_bond_config("Bonding mode: ", "\S*", bond_port)

    def get_bond_balance_policy(self, bond_port):
        """
        Get the balance transmit policy of bonding device.
        """
        return self.get_info_from_bond_config("Balance Xmit Policy: ", "\S+", bond_port)

    def get_bond_slaves(self, bond_port):
        """
        Get all the slaves of the bonding device which you choose.
        """
        try:
            return self.get_info_from_bond_config(
                "Slaves \(\d\): \[", "\d*( \d*)*", bond_port
            )
        except Exception as e:
            return self.get_info_from_bond_config("Slaves: \[", "\d*( \d*)*", bond_port)

    def get_bond_active_slaves(self, bond_port):
        """
        Get the active slaves of the bonding device which you choose.
        """
        try:
            return self.get_info_from_bond_config(
                "Active Slaves \(\d\): \[", "\d*( \d*)*", bond_port
            )
        except Exception as e:
            return self.get_info_from_bond_config(
                "Acitve Slaves: \[", "\d*( \d*)*", bond_port
            )

    def get_bond_primary(self, bond_port):
        """
        Get the primary slave of the bonding device which you choose.
        """
        return self.get_info_from_bond_config("Current Primary: \[", "\d*", bond_port)

    def create_bonded_device(self, mode="", socket=0, verify_detail=False):
        """
        Create a bonding device with the parameters you specified.
        """
        p = r"\w+\((\d+)\)"
        mode_id = int(re.match(p, mode).group(1))
        out = self.dut.send_expect(
            "create bonded device %s %d" % (mode_id, socket), "testpmd> "
        )
        self.verify(
            "Created new bonded device" in out,
            "Create bonded device on mode [%s] socket [%d] failed" % (mode, socket),
        )
        bond_port = self.get_value_from_str(
            "Created new bonded device net_bonding_testpmd_[\d] on \(port ", "\d+", out
        )
        bond_port = int(bond_port)

        if verify_detail:
            out = self.dut.send_expect(
                "show bonding config %d" % bond_port, "testpmd> "
            )
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
                "Primary: []" not in out,
                "Primary display error when create bonded device",
            )

            out = self.dut.send_expect("show port info %d" % bond_port, "testpmd> ")
            self.verify(
                "Connect to socket: %d" % socket in out,
                "Bonding port connect socket error",
            )
            self.verify(
                "Link status: down" in out, "Bonding port default link status error"
            )
            self.verify(
                "Link speed: None" in out, "Bonding port default link speed error"
            )

        return bond_port

    def start_port(self, port):
        """
        Start a port which the testpmd can see.
        """
        self.pmdout.execute_cmd("port start %s" % str(port))

    def add_slave_to_bonding_device(self, bond_port, invert_verify=False, *slave_port):
        """
        Add the ports into the bonding device as slaves.
        """
        if len(slave_port) <= 0:
            utils.RED("No port exist when add slave to bonded device")
        for slave_id in slave_port:
            self.pmdout.execute_cmd("add bonding slave %d %d" % (slave_id, bond_port))
            slaves = self.get_info_from_bond_config(
                "Slaves \(\d\): \[", "\d*( \d*)*", bond_port
            )
            if not invert_verify:
                self.verify(str(slave_id) in slaves, "Add port as bonding slave failed")
            else:
                self.verify(
                    str(slave_id) not in slaves,
                    "Add port as bonding slave successfully,should fail",
                )

    def remove_slave_from_bonding_device(
        self, bond_port, invert_verify=False, *slave_port
    ):
        """
        Remove the specified slave port from the bonding device.
        """
        if len(slave_port) <= 0:
            utils.RED("No port exist when remove slave from bonded device")
        for slave_id in slave_port:
            self.dut.send_expect(
                "remove bonding slave %d %d" % (int(slave_id), bond_port), "testpmd> "
            )
            out = self.get_info_from_bond_config("Slaves: \[", "\d*( \d*)*", bond_port)
            if not invert_verify:
                self.verify(
                    str(slave_id) not in out, "Remove slave to fail from bonding device"
                )
            else:
                self.verify(
                    str(slave_id) in out,
                    "Remove slave successfully from bonding device,should be failed",
                )

    def remove_all_slaves(self, bond_port):
        """
        Remove all slaves of specified bound device.
        """
        all_slaves = self.get_bond_slaves(bond_port)
        all_slaves = all_slaves.split()
        if len(all_slaves) == 0:
            pass
        else:
            self.remove_slave_from_bonding_device(bond_port, False, *all_slaves)

    def set_primary_for_bonding_device(
        self, bond_port, slave_port, invert_verify=False
    ):
        """
        Set the primary slave for the bonding device.
        """
        self.dut.send_expect(
            "set bonding primary %d %d" % (slave_port, bond_port), "testpmd> "
        )
        out = self.get_info_from_bond_config("Primary: \[", "\d*", bond_port)
        if not invert_verify:
            self.verify(str(slave_port) in out, "Set bonding primary port failed")
        else:
            self.verify(
                str(slave_port) not in out,
                "Set bonding primary port successfully,should not success",
            )

    def set_mode_for_bonding_device(self, bond_port, mode_id):
        """
        Set the mode for the bonding device.
        """
        self.dut.send_expect(
            "set bonding mode %d %d" % (mode_id, bond_port), "testpmd> "
        )
        mode_value = self.get_bond_mode(bond_port)
        self.verify(str(mode_id) in mode_value, "Set bonding mode failed")

    def set_mac_for_bonding_device(self, bond_port, mac):
        """
        Set the MAC for the bonding device.
        """
        self.dut.send_expect(
            "set bonding mac_addr %s %s" % (bond_port, mac), "testpmd> "
        )
        new_mac = self.get_port_mac(bond_port)
        self.verify(new_mac == mac, "Set bonding mac failed")

    def set_balance_policy_for_bonding_device(self, bond_port, policy):
        """
        Set the balance transmit policy for the bonding device.
        """
        self.dut.send_expect(
            "set bonding balance_xmit_policy %d %s" % (bond_port, policy), "testpmd> "
        )
        new_policy = self.get_bond_balance_policy(bond_port)
        policy = "BALANCE_XMIT_POLICY_LAYER" + policy.lstrip("l")
        self.verify(new_policy == policy, "Set bonding balance policy failed")

    def send_default_packet_to_slave(
        self, unbound_port, bond_port, pkt_count=100, **slaves
    ):
        """
        Send packets to the slaves and calculate the slave`s RX packets
        and unbond port TX packets.
        Parameters:
        *** unbound_port: the unbonded port id
        *** bond_port: the bonded device port id
        *** slaves:
        ******* 'active'=[]
        ******* 'inactive'=[]
        """
        summary = 0

        # send to slave ports
        pkt_orig = self.get_all_stats(unbound_port, "tx", bond_port, **slaves)
        for slave in slaves["active"]:
            temp_count = self.send_packet(
                self.vf_ports[slave], False, FRAME_SIZE_64, pkt_count
            )
            summary += temp_count
        for slave in slaves["inactive"]:
            self.send_packet(
                self.vf_ports[slave], False, FRAME_SIZE_64, pkt_count, True
            )
        time.sleep(1)
        pkt_now = self.get_all_stats(unbound_port, "tx", bond_port, **slaves)

        for key in pkt_now:
            for num in [0, 1, 2]:
                pkt_now[key][num] -= pkt_orig[key][num]

        return pkt_now, summary

    def send_customized_packet_to_slave(
        self, unbound_port, bond_port, *pkt_info, **slaves
    ):
        """
        Send packets to the slaves and calculate the slave`s RX packets
        and unbond port TX packets.
        Parameters:
        *** unbound_port: the unbonded port id
        *** bond_port: the bonded device port id
        *** pkt_info: the first is necessary which will describe the packet,
                      the second is optional which will describe the params of
                      the function send_packet
        *** slaves:
        ******* 'active'=[]
        ******* 'inactive'=[]
        """
        pkt_orig = {}
        pkt_now = {}
        temp_count = 0
        summary = 0

        pkt_info_len = len(pkt_info)
        if pkt_info_len < 1:
            self.verify(False, "At least one members for pkt_info!")

        ether_ip = pkt_info[0]
        if pkt_info_len > 1:
            pkt_size = pkt_info[1].get("frame_size", FRAME_SIZE_64)
            pkt_count = pkt_info[1].get("pkt_count", 1)
            invert_verify = pkt_info[1].get("verify", False)
        else:
            pkt_size = FRAME_SIZE_64
            pkt_count = 1
            invert_verify = False

        # send to slave ports
        pkt_orig = self.get_all_stats(unbound_port, "tx", bond_port, **slaves)
        for slave in slaves["active"]:
            temp_count = self.send_packet(
                self.vf_ports[slave],
                False,
                pkt_size,
                pkt_count,
                invert_verify,
                **ether_ip,
            )
            summary += temp_count
        for slave in slaves["inactive"]:
            self.send_packet(
                self.vf_ports[slave], False, FRAME_SIZE_64, pkt_count, True
            )
        pkt_now = self.get_all_stats(unbound_port, "tx", bond_port, **slaves)

        for key in pkt_now:
            for num in [0, 1, 2]:
                pkt_now[key][num] -= pkt_orig[key][num]

        return pkt_now, summary

    def send_default_packet_to_unbound_port(
        self, unbound_port, bond_port, pkt_count, **slaves
    ):
        """
        Send packets to the unbound port and calculate unbound port RX packets
        and the slave`s TX packets.
        Parameters:
        *** unbound_port: the unbonded port id
        *** bond_port: the bonded device port id
        *** slaves:
        ******* 'active':[]
        ******* 'inactive':[]
        """
        pkt_orig = {}
        pkt_now = {}
        summary = 0

        # send to unbonded device
        pkt_orig = self.get_all_stats(unbound_port, "rx", bond_port, **slaves)
        summary = self.send_packet(unbound_port, False, FRAME_SIZE_64, pkt_count)
        pkt_now = self.get_all_stats(unbound_port, "rx", bond_port, **slaves)

        for key in pkt_now:
            for num in [0, 1, 2]:
                pkt_now[key][num] -= pkt_orig[key][num]

        return pkt_now, summary

    def send_customized_packet_to_unbound_port(
        self, unbound_port, bond_port, policy, vlan_tag=False, pkt_count=100, **slaves
    ):
        """
        Verify that transmitting the packets correctly in the XOR mode.
        Parameters:
        *** unbound_port: the unbonded port id
        *** bond_port: the bonded device port id
        *** policy:'L2' , 'L23' or 'L34'
        *** vlan_tag:False or True
        *** slaves:
        ******* 'active'=[]
        ******* 'inactive'=[]
        """
        pkt_orig = {}
        pkt_now = {}
        summary = 0
        temp_count = 0

        # send to unbound_port
        pkt_orig = self.get_all_stats(unbound_port, "rx", bond_port, **slaves)
        query_type = "mac"
        dest_mac = self.bond_inst.get_port_mac(self.vf_ports[unbound_port], query_type)
        dest_ip = "10.239.129.88"
        dest_port = 53

        global D_MAC_IP_PORT
        D_MAC_IP_PORT = [dest_mac, dest_ip, dest_port]

        ether_ip = {}
        ether = {}
        ip = {}
        udp = {}

        ether["dest_mac"] = False
        ip["dest_ip"] = dest_ip
        udp["dest_port"] = 53
        if vlan_tag:
            dot1q = {}
            dot1q["vlan"] = random.randint(1, 50)
            ether_ip["dot1q"] = dot1q

        ether_ip["ether"] = ether
        ether_ip["ip"] = ip
        ether_ip["udp"] = udp

        global S_MAC_IP_PORT
        source = S_MAC_IP_PORT

        for src_mac, src_ip, src_port in source:
            ether_ip["ether"]["src_mac"] = src_mac
            ether_ip["ip"]["src_ip"] = src_ip
            ether_ip["udp"]["src_port"] = src_port
            temp_count = self.send_packet(
                unbound_port, False, FRAME_SIZE_64, pkt_count, False, **ether_ip
            )
            summary += temp_count
        pkt_now = self.get_all_stats(unbound_port, "rx", bond_port, **slaves)

        for key in pkt_now:
            for num in [0, 1, 2]:
                pkt_now[key][num] -= pkt_orig[key][num]

        return pkt_now, summary

    #
    # Test cases.
    #
    def set_up_all(self):
        """
        Run before each test suite
        """
        self.verify("bsdapp" not in self.target, "Bonding not support freebsd")
        self.frame_sizes = [64, 65, 128, 256, 512, 1024, 1280, 1518]

        self.eth_head_size = 18
        self.ip_head_size = 20
        self.udp_header_size = 8
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 4, "Insufficient ports")
        self.dport_info0 = self.dut.ports_info[self.dut_ports[0]]
        self.dport_ifaces0 = self.dport_info0["intf"]
        self.dport_info1 = self.dut.ports_info[self.dut_ports[1]]
        self.dport_ifaces1 = self.dport_info1["intf"]
        tester_port0 = self.tester.get_local_port(self.dut_ports[0])
        self.tport_iface0 = self.tester.get_interface(tester_port0)
        tester_port1 = self.tester.get_local_port(self.dut_ports[1])
        self.tport_iface1 = self.tester.get_interface(tester_port1)
        self.flag = "link-down-on-close"
        self.default_stats = self.tester.get_priv_flags_state(
            self.tport_iface0, self.flag
        )
        if self.default_stats:
            for port in self.dut_ports:
                tester_port = self.tester.get_local_port(port)
                tport_iface = self.tester.get_interface(tester_port)
                self.tester.send_expect(
                    "ethtool --set-priv-flags %s %s on" % (tport_iface, self.flag), "# "
                )
        self.create_vfs(pfs_id=self.dut_ports, vf_num=1)
        self.vf_ports = list(range(len(self.vfs_pci)))
        self.pmdout = PmdOutput(self.dut)

        self.tester_bond = "bond0"
        # initialize bonding common methods name
        config = {
            "parent": self,
            "pkt_name": "udp",
            "pkt_size": FRAME_SIZE_64,
            "src_mac": "52:00:00:00:00:03",
            "src_ip": "10.239.129.65",
            "src_port": 61,
            "dst_ip": "10.239.129.88",
            "dst_port": 53,
        }
        self.bond_inst = bonding.PmdBonding(**config)

    def set_up(self):
        """
        Run before each test case.
        """
        if self.running_case in ["test_bound_promisc_opt", "test_tlb_basic"]:
            self.dut.send_expect(
                "ip link set %s vf 0 trust on" % (self.dport_ifaces0), "# "
            )
        self.pmdout.start_testpmd(
            cores="1S/4C/1T",
            ports=self.vfs_pci,
        )

    def create_vfs(self, pfs_id, vf_num):
        self.sriov_vfs_port = []
        self.vfs_pci = []
        self.dut.bind_interfaces_linux(self.kdriver)
        pfs_id = pfs_id if isinstance(pfs_id, list) else [pfs_id]
        for pf_id in pfs_id:
            self.dut.generate_sriov_vfs_by_port(pf_id, vf_num)
            self.sriov_vfs_port += self.dut.ports_info[self.dut_ports[pf_id]][
                "vfs_port"
            ]
            dport_iface = self.dut.ports_info[self.dut_ports[pf_id]]["intf"]
            self.dut.send_expect(
                "ip link set %s vf 0 spoofchk off" % (dport_iface), "# "
            )
        for vf in self.sriov_vfs_port:
            self.vfs_pci.append(vf.pci)
        try:
            for port in self.sriov_vfs_port:
                port.bind_driver(self.drivername)

        except Exception as e:
            self.dut.destroy_all_sriov_vfs()
            raise Exception(e)

    def verify_bound_basic_opt(self, mode_set):
        """
        Do some basic operations to bonded devices and slaves,
        such as adding, removing, setting primary or setting mode.
        """
        p = r"\w+\((\d+)\)"
        mode_id = int(re.match(p, mode_set).group(1))
        bond_port_0 = self.create_bonded_device(mode_set, SOCKET_0, True)
        self.add_slave_to_bonding_device(bond_port_0, False, self.vf_ports[1])

        mode_value = self.get_bond_mode(bond_port_0)
        self.verify("%s" % mode_set in mode_value, "Setting bonding mode error")

        bond_port_1 = self.create_bonded_device(mode_set, SOCKET_0)
        self.add_slave_to_bonding_device(bond_port_0, False, self.vf_ports[0])
        self.add_slave_to_bonding_device(bond_port_1, True, self.vf_ports[0])

        OTHER_MODE = mode_id + 1 if not mode_id else mode_id - 1
        self.set_mode_for_bonding_device(bond_port_0, OTHER_MODE)
        self.set_mode_for_bonding_device(bond_port_0, mode_id)

        self.add_slave_to_bonding_device(bond_port_0, False, self.vf_ports[2])
        time.sleep(3)
        self.set_primary_for_bonding_device(bond_port_0, self.vf_ports[2])

        self.remove_slave_from_bonding_device(bond_port_0, False, self.vf_ports[2])
        primary_now = self.get_bond_primary(bond_port_0)
        self.verify(
            int(primary_now) == self.vf_ports[1],
            "Reset primary slave failed after removing primary slave",
        )

        for bond_port in [bond_port_0, bond_port_1]:
            self.remove_all_slaves(bond_port)

        self.dut.send_expect("quit", "# ")
        self.pmdout.start_testpmd(
            cores="1S/4C/1T",
            ports=self.vfs_pci,
        )

    def verify_bound_mac_opt(self, mode_set):
        """
        Create bonded device, add one slave,
        verify bonded device MAC action varies with the mode.
        """
        mac_address_0_orig = self.get_port_mac(self.vf_ports[0])
        mac_address_1_orig = self.get_port_mac(self.vf_ports[1])
        mac_address_2_orig = self.get_port_mac(self.vf_ports[2])
        mac_address_3_orig = self.get_port_mac(self.vf_ports[3])

        bond_port = self.create_bonded_device(mode_set, SOCKET_1)
        self.add_slave_to_bonding_device(bond_port, False, self.vf_ports[1])

        mac_address_bond_orig = self.get_port_mac(bond_port)
        self.verify(
            mac_address_1_orig == mac_address_bond_orig,
            "Bonded device MAC address not same with first slave MAC",
        )

        self.add_slave_to_bonding_device(bond_port, False, self.vf_ports[2])
        mac_address_2_now = self.get_port_mac(self.vf_ports[2])
        mac_address_bond_now = self.get_port_mac(bond_port)
        if mode_set in [MODE_ROUND_ROBIN, MODE_XOR_BALANCE, MODE_BROADCAST]:
            self.verify(
                mac_address_1_orig == mac_address_bond_now
                and mac_address_bond_now == mac_address_2_now,
                "NOT all slaves MAC address same with bonding device in mode %s"
                % mode_set,
            )
        else:
            self.verify(
                mac_address_1_orig == mac_address_bond_now
                and mac_address_bond_now != mac_address_2_now,
                "All slaves should not be the same in mode %s" % mode_set,
            )

        new_mac = "00:11:22:00:33:44"
        self.set_mac_for_bonding_device(bond_port, new_mac)
        self.start_port(bond_port)
        mac_address_1_now = self.get_port_mac(self.vf_ports[1])
        mac_address_2_now = self.get_port_mac(self.vf_ports[2])
        mac_address_bond_now = self.get_port_mac(bond_port)
        if mode_set in [MODE_ROUND_ROBIN, MODE_XOR_BALANCE, MODE_BROADCAST]:
            self.verify(
                mac_address_1_now
                == mac_address_2_now
                == mac_address_bond_now
                == new_mac,
                "Set mac failed for bonding device in mode %s" % mode_set,
            )
        elif mode_set == MODE_LACP:
            self.verify(
                mac_address_bond_now == new_mac
                and mac_address_1_now != new_mac
                and mac_address_2_now != new_mac
                and mac_address_1_now != mac_address_2_now,
                "Set mac failed for bonding device in mode %s" % mode_set,
            )
        elif mode_set in [MODE_ACTIVE_BACKUP, MODE_TLB_BALANCE]:
            self.verify(
                mac_address_bond_now == new_mac
                and mac_address_1_now == new_mac
                and mac_address_bond_now != mac_address_2_now,
                "Set mac failed for bonding device in mode %s" % mode_set,
            )

        self.set_primary_for_bonding_device(bond_port, self.vf_ports[2], False)
        mac_address_1_now = self.get_port_mac(self.vf_ports[1])
        mac_address_2_now = self.get_port_mac(self.vf_ports[2])
        mac_address_bond_now = self.get_port_mac(bond_port)
        self.verify(
            mac_address_bond_now == new_mac, "Slave MAC changed when set primary slave"
        )

        mac_address_1_orig = mac_address_1_now
        self.remove_slave_from_bonding_device(bond_port, False, self.vf_ports[2])
        mac_address_2_now = self.get_port_mac(self.vf_ports[2])
        self.verify(
            mac_address_2_now == mac_address_2_orig,
            "MAC not back to original after removing the port",
        )

        mac_address_1_now = self.get_port_mac(self.vf_ports[1])
        mac_address_bond_now = self.get_port_mac(bond_port)
        self.verify(
            mac_address_bond_now == new_mac and mac_address_1_now == mac_address_1_orig,
            "Bonding device or slave MAC changed after removing the primary slave",
        )

        self.remove_all_slaves(bond_port)
        self.dut.send_expect("quit", "# ")
        self.pmdout.start_testpmd(
            cores="1S/4C/1T",
            ports=self.vfs_pci,
        )

    def verify_bound_promisc_opt(self, mode_set):
        """
        Set promiscuous mode on bonded device, verify bonded device and all slaves
        have different actions by the different modes.
        """
        unbound_port = self.vf_ports[3]
        bond_port = self.create_bonded_device(mode_set, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (unbound_port, bond_port), "testpmd> "
        )
        self.start_port(bond_port)
        self.dut.send_expect("start", "testpmd> ")

        port_disabled_num = 0
        testpmd_all_ports = self.vf_ports
        testpmd_all_ports.append(bond_port)
        for port_id in testpmd_all_ports:
            value = self.get_detail_from_port_info(
                "Promiscuous mode: ", "enabled", port_id
            )
            if not value:
                port_disabled_num += 1
        self.verify(
            port_disabled_num == 0,
            "Not all slaves of bonded device turn promiscuous mode on by default.",
        )

        ether_ip = {}
        ether = {}
        ether["dest_mac"] = "00:11:22:33:44:55"
        ether_ip["ether"] = ether

        send_param = {}
        pkt_count = 1
        send_param["pkt_count"] = pkt_count
        pkt_info = [ether_ip, send_param]

        slaves = {}
        slaves["active"] = [self.vf_ports[0]]
        slaves["inactive"] = []
        curr_primary = self.vf_ports[0]

        pkt_now, summary = self.send_customized_packet_to_slave(
            unbound_port, bond_port, *pkt_info, **slaves
        )
        if mode_set == MODE_LACP:
            do_transmit = False
            pkt_size = 0
            if pkt_now[unbound_port][0]:
                do_transmit = True
                pkt_size = pkt_now[unbound_port][2] / pkt_now[unbound_port][0]
            self.verify(
                do_transmit and pkt_size != LACP_MESSAGE_SIZE,
                "Data not received by slave or bonding device when promiscuous enabled",
            )
        else:
            self.verify(
                pkt_now[self.vf_ports[0]][0] == pkt_now[bond_port][0]
                and pkt_now[bond_port][0] == pkt_count,
                "Data not received by slave or bonding device when promiscuous enabled",
            )

        self.dut.send_expect("set promisc %s off" % bond_port, "testpmd> ")
        port_disabled_num = 0
        testpmd_all_ports = [
            self.vf_ports[0],
            self.vf_ports[1],
            self.vf_ports[2],
            bond_port,
        ]
        for port_id in testpmd_all_ports:
            value = self.get_detail_from_port_info(
                "Promiscuous mode: ", "disabled", port_id
            )
            if value == "disabled":
                port_disabled_num += 1
        if mode_set in [MODE_ROUND_ROBIN, MODE_XOR_BALANCE, MODE_BROADCAST]:
            self.verify(
                port_disabled_num == 4,
                "Not all slaves of bonded device turn promiscuous mode off in mode %s."
                % mode_set,
            )
        elif mode_set == MODE_LACP:
            self.verify(
                port_disabled_num == 1,
                "Not only turn bound device promiscuous mode off in mode %s" % mode_set,
            )
        else:
            self.verify(
                port_disabled_num == 2,
                "Not only the primary slave turn promiscous mode off in mode %s, "
                % mode_set
                + " when bonded device  promiscous disabled.",
            )
            curr_primary = int(self.get_bond_primary(bond_port))
            slaves["active"] = [curr_primary]

        if mode_set != MODE_LACP:
            send_param["verify"] = True
        pkt_now, summary = self.send_customized_packet_to_slave(
            unbound_port, bond_port, *pkt_info, **slaves
        )
        if mode_set == MODE_LACP:
            do_transmit = False
            pkt_size = 0
            if pkt_now[unbound_port][0]:
                do_transmit = True
                pkt_size = pkt_now[unbound_port][2] / pkt_now[unbound_port][0]
            self.verify(
                not do_transmit or pkt_size == LACP_MESSAGE_SIZE,
                "Data received by slave or bonding device when promiscuous disabled",
            )
        else:
            self.verify(
                pkt_now[curr_primary][0] == 0 and pkt_now[bond_port][0] == 0,
                "Data received by slave or bonding device when promiscuous disabled",
            )

        pkt_now, summary = self.send_default_packet_to_slave(
            self.vf_ports[3], bond_port, pkt_count, **slaves
        )
        if mode_set == MODE_LACP:
            do_transmit = False
            pkt_size = 0
            if pkt_now[unbound_port][0]:
                do_transmit = True
                pkt_size = pkt_now[unbound_port][2] / pkt_now[unbound_port][0]
            self.verify(
                not do_transmit or pkt_size != LACP_MESSAGE_SIZE,
                "RX or TX packet number not correct when promiscuous disabled",
            )
        else:
            self.verify(
                pkt_now[curr_primary][0] == pkt_now[bond_port][0]
                and pkt_now[self.vf_ports[3]][0] == pkt_now[bond_port][0]
                and pkt_now[bond_port][0] == pkt_count,
                "RX or TX packet number not correct when promiscuous disabled",
            )

        # Stop fwd threads first before removing slaves from bond to avoid
        # races and crashes
        self.dut.send_expect("stop", "testpmd> ")
        self.remove_all_slaves(bond_port)
        self.dut.send_expect("quit", "# ")

    def test_bound_basic_opt(self):
        """
        Test Case1: Basic bonding--Create bonded devices and slaves
        """
        self.verify_bound_basic_opt(MODE_ACTIVE_BACKUP)

    def test_bound_mac_opt(self):
        """
        Test Case2: Basic bonding--MAC Address Test
        """
        self.verify_bound_mac_opt(MODE_BROADCAST)

    def test_bound_promisc_opt(self):
        """
        Test Case3: Basic bonding--Device Promiscuous Mode Test
        """
        self.verify_bound_promisc_opt(MODE_BROADCAST)

    def admin_tester_port(self, local_port, status):
        """
        Do some operations to the network interface port, such as "up" or "down".
        """
        if self.tester.get_os_type() == "freebsd":
            self.tester.admin_ports(local_port, status)
        else:
            eth = self.tester.get_interface(local_port)
            self.tester.admin_ports_linux(eth, status)
        time.sleep(10)

    def verify_round_robin_rx(self, unbound_port, bond_port, **slaves):
        """
        Verify the receiving packet are all correct in the round robin mode.
            slaves:
                'active' = []
                'inactive' = []
        """
        pkt_count = 100
        pkt_now = {}
        pkt_now, summary = self.send_default_packet_to_slave(
            unbound_port, bond_port, pkt_count=pkt_count, **slaves
        )

        self.verify(
            pkt_now[unbound_port][0] == pkt_count * slaves["active"].__len__(),
            "Unbonded port has error TX pkt count in mode 0",
        )
        self.verify(
            pkt_now[bond_port][0] == pkt_count * slaves["active"].__len__(),
            "Bonding port has error RX pkt count in mode 0",
        )

    def verify_round_robin_tx(self, unbound_port, bond_port, **slaves):
        """
        Verify the transmitting packet are all correct in the round robin mode.
            slaves:
                'active' = []
                'inactive' = []
        """
        pkt_count = 300
        pkt_now = {}
        pkt_now, summary = self.send_default_packet_to_unbound_port(
            unbound_port, bond_port, pkt_count=pkt_count, **slaves
        )

        if slaves["active"].__len__() == 0:
            self.verify(
                pkt_now[bond_port][0] == 0,
                "Bonding port should not have TX pkt in mode 0 when all slaves down",
            )
        else:
            self.verify(
                pkt_now[bond_port][0] == pkt_count,
                "Bonding port has error TX pkt count in mode 0",
            )
        for slave in slaves["active"]:
            self.verify(
                pkt_now[slave][0] == pkt_count / slaves["active"].__len__(),
                "Active slave has error TX pkt count in mode 0",
            )
        for slave in slaves["inactive"]:
            self.verify(
                pkt_now[slave][0] == 0,
                "Inactive slave has error TX pkt count in mode 0",
            )

    def test_round_robin_rx_tx(self):
        """
        Test Case4: Mode 0(Round Robin) TX/RX test
        """
        bond_port = self.create_bonded_device(MODE_ROUND_ROBIN, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")

        slaves = {}
        slaves["active"] = [self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]]
        slaves["inactive"] = []
        self.verify_round_robin_rx(self.vf_ports[3], bond_port, **slaves)
        self.verify_round_robin_tx(self.vf_ports[3], bond_port, **slaves)

    def test_round_robin_one_slave_down(self):
        """
        Test Case5: Mode 0(Round Robin) Bring one slave link down
        """
        self.verify(self.default_stats, "tester port not support '%s'" % self.flag)
        bond_port = self.create_bonded_device(MODE_ROUND_ROBIN, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "down")

        stat = self.tester.get_port_status(
            self.tester.get_local_port(self.dut_ports[0])
        )
        self.dut.send_expect("show bonding config %d" % bond_port, "testpmd> ")
        self.dut.send_expect("show port info all", "testpmd> ")

        try:
            slaves = {}
            slaves["active"] = [self.vf_ports[1], self.vf_ports[2]]
            slaves["inactive"] = [self.vf_ports[0]]
            self.verify_round_robin_rx(self.vf_ports[3], bond_port, **slaves)
            self.verify_round_robin_tx(self.vf_ports[3], bond_port, **slaves)
        finally:
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "up")

    def test_round_robin_all_slaves_down(self):
        """
        Test Case6: Mode 0(Round Robin) Bring all slave links down
        """
        bond_port = self.create_bonded_device(MODE_ROUND_ROBIN, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")

        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "down")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[1]), "down")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[2]), "down")

        try:
            slaves = {}
            slaves["active"] = []
            slaves["inactive"] = [
                self.vf_ports[0],
                self.vf_ports[1],
                self.vf_ports[2],
            ]
            self.verify_round_robin_rx(self.vf_ports[3], bond_port, **slaves)
            self.verify_round_robin_tx(self.vf_ports[3], bond_port, **slaves)
        finally:
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "up")
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[1]), "up")
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[2]), "up")

    def get_all_stats(self, unbound_port, rx_tx, bond_port, **slaves):
        """
        Get all the port stats which the testpmd can discover.
        Parameters:
        *** unbound_port: pmd port id
        *** rx_tx: unbond port stat 'rx' or 'tx'
        *** bond_port: bonding port
        *** slaves:
        ******** 'active' = []
        ******** 'inactive' = []
        """
        pkt_now = {}

        if rx_tx == "rx":
            bond_stat = "tx"
        else:
            bond_stat = "rx"

        pkt_now[unbound_port] = [int(_) for _ in self.get_stats(unbound_port, rx_tx)]
        pkt_now[bond_port] = [int(_) for _ in self.get_stats(bond_port, bond_stat)]
        for slave in slaves["active"]:
            pkt_now[slave] = [int(_) for _ in self.get_stats(slave, bond_stat)]
        for slave in slaves["inactive"]:
            pkt_now[slave] = [int(_) for _ in self.get_stats(slave, bond_stat)]

        return pkt_now

    def verify_active_backup_rx(self, unbound_port, bond_port, **slaves):
        """
        Verify the RX packets are all correct in the active-backup mode.
        Parameters:
        *** slaves:
        ******* 'active' = []
        ******* 'inactive' = []
        """
        pkt_count = 100
        pkt_now = {}

        slave_num = slaves["active"].__len__()
        if slave_num != 0:
            active_flag = 1
        else:
            active_flag = 0

        pkt_now, summary = self.send_default_packet_to_slave(
            unbound_port, bond_port, pkt_count=pkt_count, **slaves
        )

        self.verify(
            pkt_now[bond_port][0] == pkt_count * slave_num,
            "Not correct RX pkt on bond port in mode 1",
        )
        self.verify(
            pkt_now[unbound_port][0] == pkt_count * active_flag,
            "Not correct TX pkt on unbound port in mode 1",
        )
        for slave in slaves["inactive"]:
            self.verify(
                pkt_now[slave][0] == 0, "Not correct RX pkt on inactive port in mode 1"
            )
        for slave in slaves["active"]:
            self.verify(
                pkt_now[slave][0] == pkt_count,
                "Not correct RX pkt on active port in mode 1",
            )

    def verify_active_backup_tx(self, unbound_port, bond_port, **slaves):
        """
        Verify the TX packets are all correct in the active-backup mode.
        Parameters:
        *** slaves:
        ******* 'active' = []
        ******* 'inactive' = []
        """
        pkt_count = 0
        pkt_now = {}

        if slaves["active"].__len__() != 0:
            primary_port = slaves["active"][0]
            active_flag = 1
        else:
            active_flag = 0

        pkt_now, summary = self.send_default_packet_to_unbound_port(
            unbound_port, bond_port, pkt_count=pkt_count, **slaves
        )

        self.verify(
            pkt_now[bond_port][0] == pkt_count * active_flag,
            "Not correct RX pkt on bond port in mode 1",
        )
        if active_flag == 1:
            self.verify(
                pkt_now[primary_port][0] == pkt_count,
                "Not correct TX pkt on primary port in mode 1",
            )
        for slave in slaves["inactive"]:
            self.verify(
                pkt_now[slave][0] == 0, "Not correct TX pkt on inactive port in mode 1"
            )
        for slave in [slave for slave in slaves["active"] if slave != primary_port]:
            self.verify(
                pkt_now[slave][0] == 0, "Not correct TX pkt on backup port in mode 1"
            )

    def test_active_backup_rx_tx(self):
        """
        Test Case7: Mode 1(Active Backup) TX/RX Test
        """
        bond_port = self.create_bonded_device(MODE_ACTIVE_BACKUP, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")
        time.sleep(5)

        slaves = {}
        slaves["active"] = [self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]]
        slaves["inactive"] = []
        self.verify_active_backup_rx(self.vf_ports[3], bond_port, **slaves)
        self.verify_active_backup_tx(self.vf_ports[3], bond_port, **slaves)

    def test_active_backup_change_primary(self):
        """
        Test Case8: Mode 1(Active Backup) Change active slave, RX/TX test
        """
        bond_port = self.create_bonded_device(MODE_ACTIVE_BACKUP, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")
        self.set_primary_for_bonding_device(bond_port, self.vf_ports[1])
        time.sleep(5)

        slaves = {}
        slaves["active"] = [self.vf_ports[1], self.vf_ports[0], self.vf_ports[2]]
        slaves["inactive"] = []
        self.verify_active_backup_rx(self.vf_ports[3], bond_port, **slaves)
        self.verify_active_backup_tx(self.vf_ports[3], bond_port, **slaves)

    def test_active_backup_one_slave_down(self):
        """
        Test Case9: Mode 1(Active Backup) Link up/down active eth dev
        """
        self.verify(self.default_stats, "tester port not support '%s'" % self.flag)
        bond_port = self.create_bonded_device(MODE_ACTIVE_BACKUP, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "down")
        primary_port = int(self.get_bond_primary(bond_port))

        try:
            slaves = {}
            active_slaves = [self.vf_ports[1], self.vf_ports[2]]
            active_slaves.remove(primary_port)
            slaves["active"] = [primary_port]
            slaves["active"].extend(active_slaves)
            slaves["inactive"] = [self.vf_ports[0]]
            self.verify_active_backup_rx(self.vf_ports[3], bond_port, **slaves)
            self.verify_active_backup_tx(self.vf_ports[3], bond_port, **slaves)
        finally:
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "up")

    def test_active_backup_all_slaves_down(self):
        """
        Test Case10: Mode 1(Active Backup) Bring all slave links down
        """
        self.verify(self.default_stats, "tester port not support '%s'" % self.flag)
        bond_port = self.create_bonded_device(MODE_ACTIVE_BACKUP, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "down")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[1]), "down")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[2]), "down")

        try:
            slaves = {}
            slaves["active"] = []
            slaves["inactive"] = [
                self.vf_ports[0],
                self.vf_ports[1],
                self.vf_ports[2],
            ]
            self.verify_active_backup_rx(self.vf_ports[3], bond_port, **slaves)
            self.verify_active_backup_tx(self.vf_ports[3], bond_port, **slaves)
        finally:
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "up")
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[1]), "up")
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[2]), "up")

    def translate_mac_str_into_int(self, mac_str):
        """
        Translate the MAC type from the string into the int.
        """
        mac_hex = "0x"
        for mac_part in mac_str.split(":"):
            mac_hex += mac_part
        return int(mac_hex, 16)

    def mac_hash(self, dest_mac, src_mac):
        """
        Generate the hash value with the source and destination MAC.
        """
        dest_port_mac = self.translate_mac_str_into_int(dest_mac)
        src_port_mac = self.translate_mac_str_into_int(src_mac)
        src_xor_dest = dest_port_mac ^ src_port_mac
        xor_value_1 = src_xor_dest >> 32
        xor_value_2 = (src_xor_dest >> 16) ^ (xor_value_1 << 16)
        xor_value_3 = src_xor_dest ^ (xor_value_1 << 32) ^ (xor_value_2 << 16)
        return htons(xor_value_1 ^ xor_value_2 ^ xor_value_3)

    def translate_ip_str_into_int(self, ip_str):
        """
        Translate the IP type from the string into the int.
        """
        ip_part_list = ip_str.split(".")
        ip_part_list.reverse()
        num = 0
        ip_int = 0
        for ip_part in ip_part_list:
            ip_part_int = int(ip_part) << (num * 8)
            ip_int += ip_part_int
            num += 1
        return ip_int

    def ipv4_hash(self, dest_ip, src_ip):
        """
        Generate the hash value with the source and destination IP.
        """
        dest_ip_int = self.translate_ip_str_into_int(dest_ip)
        src_ip_int = self.translate_ip_str_into_int(src_ip)
        return htonl(dest_ip_int ^ src_ip_int)

    def udp_hash(self, dest_port, src_port):
        """
        Generate the hash value with the source and destination port.
        """
        return htons(dest_port ^ src_port)

    def policy_and_slave_hash(self, policy, **slaves):
        """
        Generate the hash value by the policy and active slave number.
        *** policy:'L2' , 'L23' or 'L34'
        *** slaves:
        ******* 'active'=[]
        ******* 'inactive'=[]
        """
        global S_MAC_IP_PORT
        source = S_MAC_IP_PORT

        global D_MAC_IP_PORT
        dest_mac = D_MAC_IP_PORT[0]
        dest_ip = D_MAC_IP_PORT[1]
        dest_port = D_MAC_IP_PORT[2]

        hash_values = []
        if len(slaves["active"]) != 0:
            for src_mac, src_ip, src_port in source:
                if policy == "L2":
                    hash_value = self.mac_hash(dest_mac, src_mac)
                elif policy == "L23":
                    hash_value = self.mac_hash(dest_mac, src_mac) ^ self.ipv4_hash(
                        dest_ip, src_ip
                    )
                else:
                    hash_value = self.ipv4_hash(dest_ip, src_ip) ^ self.udp_hash(
                        dest_port, src_port
                    )

                if policy in ("L23", "L34"):
                    hash_value ^= hash_value >> 16
                hash_value ^= hash_value >> 8
                hash_value = hash_value % len(slaves["active"])
                hash_values.append(hash_value)

        return hash_values

    def slave_map_hash(self, port, order_ports):
        """
        Find the hash value by the given slave port id.
        """
        if len(order_ports) == 0:
            return None
        else:
            order_ports = order_ports.split()
            return order_ports.index(str(port))

    def verify_xor_rx(self, unbound_port, bond_port, **slaves):
        """
        Verify receiving the packets correctly in the XOR mode.
        Parameters:
        *** unbound_port: the unbonded port id
        *** bond_port: the bonded device port id
        *** slaves:
        ******* 'active'=[]
        ******* 'inactive'=[]
        """
        pkt_count = 100
        pkt_now = {}

        pkt_now, summary = self.send_default_packet_to_slave(
            unbound_port, bond_port, pkt_count=pkt_count, **slaves
        )

        for slave in slaves["active"]:
            self.verify(
                pkt_now[slave][0] == pkt_count, "Slave have error RX packet in XOR"
            )
        for slave in slaves["inactive"]:
            self.verify(pkt_now[slave][0] == 0, "Slave have error RX packet in XOR")
        self.verify(
            pkt_now[unbound_port][0] == pkt_count * len(slaves["active"]),
            "Unbonded device have error TX packet in XOR",
        )

    def verify_xor_tx(self, unbound_port, bond_port, policy, vlan_tag=False, **slaves):
        """
        Verify that transmitting the packets correctly in the XOR mode.
        Parameters:
        *** unbound_port: the unbonded port id
        *** bond_port: the bonded device port id
        *** policy:'L2' , 'L23' or 'L34'
        *** vlan_tag:False or True
        *** slaves:
        ******* 'active'=[]
        ******* 'inactive'=[]
        """
        pkt_count = 100
        pkt_now = {}

        pkt_now, summary = self.send_customized_packet_to_unbound_port(
            unbound_port,
            bond_port,
            policy,
            vlan_tag=False,
            pkt_count=pkt_count,
            **slaves,
        )

        hash_values = []
        hash_values = self.policy_and_slave_hash(policy, **slaves)

        order_ports = self.get_bond_active_slaves(bond_port)
        for slave in slaves["active"]:
            slave_map_hash = self.slave_map_hash(slave, order_ports)
            self.verify(
                pkt_now[slave][0] == pkt_count * hash_values.count(slave_map_hash),
                "XOR load balance transmit error on the link up port",
            )
        for slave in slaves["inactive"]:
            self.verify(
                pkt_now[slave][0] == 0,
                "XOR load balance transmit error on the link down port",
            )

    def test_xor_tx(self):
        """
        Test Case11: Mode 2(Balance XOR) TX Load Balance test
        """
        bond_port = self.create_bonded_device(MODE_XOR_BALANCE, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")

        slaves = {}
        slaves["active"] = [self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]]
        slaves["inactive"] = []

        self.verify_xor_tx(self.vf_ports[3], bond_port, "L2", False, **slaves)

    def test_xor_tx_one_slave_down(self):
        """
        Test Case12: Mode 2(Balance XOR) TX Load Balance Link down
        """
        self.verify(self.default_stats, "tester port not support '%s'" % self.flag)
        bond_port = self.create_bonded_device(MODE_XOR_BALANCE, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[2], self.vf_ports[1]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "down")

        try:
            slaves = {}
            slaves["active"] = [self.vf_ports[1], self.vf_ports[2]]
            slaves["inactive"] = [self.vf_ports[0]]

            self.verify_xor_tx(self.vf_ports[3], bond_port, "L2", False, **slaves)
        finally:
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "up")

    def test_xor_tx_all_slaves_down(self):
        """
        Test Case13: Mode 2(Balance XOR) Bring all slave links down
        """
        self.verify(self.default_stats, "tester port not support '%s'" % self.flag)
        bond_port = self.create_bonded_device(MODE_XOR_BALANCE, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "down")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[1]), "down")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[2]), "down")

        try:
            slaves = {}
            slaves["active"] = []
            slaves["inactive"] = [
                self.vf_ports[0],
                self.vf_ports[1],
                self.vf_ports[2],
            ]

            self.verify_xor_tx(self.vf_ports[3], bond_port, "L2", False, **slaves)
        finally:
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "up")
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[1]), "up")
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[2]), "up")

    def vlan_strip_and_filter(self, action="off", *ports):
        """
        Open or shutdown the vlan strip and filter option of specified port.
        """
        for port_id in ports:
            self.dut.send_expect(
                "vlan set strip %s %d" % (action, port_id), "testpmd> "
            )
            self.dut.send_expect(
                "vlan set filter %s %d" % (action, port_id), "testpmd> "
            )

    def test_xor_l34_forward(self):
        """
        Test Case14: Mode 2(Balance XOR) Layer 3+4 forwarding
        """
        bond_port = self.create_bonded_device(MODE_XOR_BALANCE, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.set_balance_policy_for_bonding_device(bond_port, "l34")
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")

        slaves = {}
        slaves["active"] = [self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]]
        slaves["inactive"] = []

        self.verify_xor_tx(self.vf_ports[3], bond_port, "L34", False, **slaves)
        self.vlan_strip_and_filter(
            "off",
            self.vf_ports[0],
            self.vf_ports[1],
            self.vf_ports[2],
            self.vf_ports[3],
            bond_port,
        )
        self.verify_xor_tx(self.vf_ports[3], bond_port, "L34", True, **slaves)

    def test_xor_rx(self):
        """
        Test Case15: Mode 2(Balance XOR) RX test
        """
        bond_port = self.create_bonded_device(MODE_XOR_BALANCE, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")

        slaves = {}
        slaves["active"] = [self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]]
        slaves["inactive"] = []

        self.verify_xor_rx(self.vf_ports[3], bond_port, **slaves)

    def verify_broadcast_rx(self, unbound_port, bond_port, **slaves):
        """
        Verify that receiving packets correctly in the broadcast mode.
        Parameters:
        *** unbound_port: the unbonded port id
        *** bond_port: the bonded device port id
        *** slaves:
        ******* 'active':[]
        ******* 'inactive':[]
        """
        pkt_count = 100
        pkt_now = {}

        pkt_now, summary = self.send_default_packet_to_slave(
            unbound_port, bond_port, pkt_count=pkt_count, **slaves
        )

        for slave in slaves["active"]:
            self.verify(
                pkt_now[slave][0] == pkt_count, "Slave RX packet not correct in mode 3"
            )
        for slave in slaves["inactive"]:
            self.verify(pkt_now[slave][0] == 0, "Slave RX packet not correct in mode 3")
        self.verify(
            pkt_now[unbound_port][0] == pkt_count * len(slaves["active"]),
            "Unbonded port TX packet not correct in mode 3",
        )
        self.verify(
            pkt_now[bond_port][0] == pkt_count * len(slaves["active"]),
            "Bonded device RX packet not correct in mode 3",
        )

    def verify_broadcast_tx(self, unbound_port, bond_port, **slaves):
        """
        Verify that transmitting packets correctly in the broadcast mode.
        Parameters:
        *** unbound_port: the unbonded port id
        *** bond_port: the bonded device port id
        *** slaves:
        ******* 'active':[]
        ******* 'inactive':[]
        """
        pkt_count = 100
        pkt_now = {}

        pkt_now, summary = self.send_default_packet_to_unbound_port(
            unbound_port, bond_port, pkt_count=pkt_count, **slaves
        )

        for slave in slaves["active"]:
            self.verify(
                pkt_now[slave][0] == pkt_count, "Slave TX packet not correct in mode 3"
            )
        for slave in slaves["inactive"]:
            self.verify(pkt_now[slave][0] == 0, "Slave TX packet not correct in mode 3")
        self.verify(
            pkt_now[unbound_port][0] == pkt_count,
            "Unbonded port RX packet not correct in mode 3",
        )
        self.verify(
            pkt_now[bond_port][0] == pkt_count * len(slaves["active"]),
            "Bonded device TX packet not correct in mode 3",
        )

    def test_broadcast_rx_tx(self):
        """
        Test Case16: Mode 3(Broadcast) TX/RX Test
        """
        bond_port = self.create_bonded_device(MODE_BROADCAST, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")

        slaves = {}
        slaves["active"] = [self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]]
        slaves["inactive"] = []

        self.verify_broadcast_rx(self.vf_ports[3], bond_port, **slaves)
        self.verify_broadcast_tx(self.vf_ports[3], bond_port, **slaves)

    def test_broadcast_tx_one_slave_down(self):
        """
        Test Case17: Mode 3(Broadcast) Bring one slave link down
        """
        self.verify(self.default_stats, "tester port not support '%s'" % self.flag)
        bond_port = self.create_bonded_device(MODE_BROADCAST, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "down")

        try:
            slaves = {}
            slaves["active"] = [self.vf_ports[1], self.vf_ports[2]]
            slaves["inactive"] = [self.vf_ports[0]]

            self.verify_broadcast_tx(self.vf_ports[3], bond_port, **slaves)
        finally:
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "up")

    def test_broadcast_tx_all_slaves_down(self):
        """
        Test Case18: Mode 3(Broadcast) Bring all slave links down
        """
        self.verify(self.default_stats, "tester port not support '%s'" % self.flag)
        bond_port = self.create_bonded_device(MODE_BROADCAST, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "down")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[1]), "down")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[2]), "down")

        try:
            slaves = {}
            slaves["active"] = []
            slaves["inactive"] = [
                self.vf_ports[0],
                self.vf_ports[1],
                self.vf_ports[2],
            ]

            self.verify_broadcast_tx(self.vf_ports[3], bond_port, **slaves)
        finally:
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "up")
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[1]), "up")
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[2]), "up")

    def verify_tlb_rx(self, unbound_port, bond_port, **slaves):
        """
        Verify that receiving packets correctly in the mode 4.
        Parameters:
        *** unbound_port: the unbonded port id
        *** bond_port: the bonded device port id
        *** slaves:
        ******* 'active':[]
        ******* 'inactive':[]
        """
        pkt_count = 100
        pkt_now = {}

        slave_num = slaves["active"].__len__()
        if slave_num != 0:
            active_flag = 1
        else:
            active_flag = 0

        pkt_now, summary = self.send_default_packet_to_slave(
            unbound_port, bond_port, pkt_count=pkt_count, **slaves
        )

        self.verify(
            pkt_now[unbound_port][0] == pkt_count * active_flag,
            "Unbonded device has error TX packet in TLB",
        )
        self.verify(
            pkt_now[bond_port][0] == pkt_count * slave_num,
            "Bounded device has error RX packet in TLB",
        )
        for slave in slaves["inactive"]:
            self.verify(
                pkt_now[slave][0] == 0, "Inactive slave has error RX packet in TLB"
            )
        for slave in slaves["active"]:
            self.verify(
                pkt_now[slave][0] == pkt_count,
                "Active slave has error RX packet in TLB",
            )

    def verify_tlb_tx(self, unbound_port, bond_port, **slaves):
        """
        Verify that transmitting packets correctly in the broadcast mode.
        Parameters:
        *** unbound_port: the unbonded port id
        *** bond_port: the bonded device port id
        *** slaves:
        ******* 'active':[]
        ******* 'inactive':[]
        """
        pkt_count = "MANY"

        # send to unbonded device
        pkt_now, summary = self.send_default_packet_to_unbound_port(
            unbound_port, bond_port, pkt_count=pkt_count, **slaves
        )

        active_slaves = len(slaves["active"])
        if active_slaves:
            mean = float(summary) / float(active_slaves)
            active_flag = 1
        else:
            active_flag = 0

        for slave in slaves["active"]:
            self.verify(
                pkt_now[slave][0] > mean * 0.8 and pkt_now[slave][0] < mean * 1.2,
                "Slave TX packet not correct in mode 5!",
            )
        for slave in slaves["inactive"]:
            self.verify(
                pkt_now[slave][0] == 0, "Slave TX packet not correct in mode 5!!"
            )
        self.verify(
            pkt_now[unbound_port][0] == summary,
            "Unbonded port RX packet not correct in TLB",
        )
        self.verify(
            pkt_now[bond_port][0] == summary * active_flag,
            "Bonded device TX packet not correct in TLB",
        )

    def test_tlb_basic(self):
        """
        Test Case19: Mode 5(TLB) Base Test
        """
        self.verify_bound_basic_opt(MODE_TLB_BALANCE)
        self.verify_bound_mac_opt(MODE_TLB_BALANCE)
        self.verify_bound_promisc_opt(MODE_TLB_BALANCE)

    def test_tlb_rx_tx(self):
        """
        Test Case20: Mode 5(TLB) TX/RX test
        """
        bond_port = self.create_bonded_device(MODE_TLB_BALANCE, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")

        slaves = {}
        slaves["active"] = [self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]]
        slaves["inactive"] = []

        self.verify_tlb_rx(self.vf_ports[3], bond_port, **slaves)
        self.verify_tlb_tx(self.vf_ports[3], bond_port, **slaves)

    def test_tlb_one_slave_dwon(self):
        """
        Test Case21: Mode 5(TLB) Bring one slave link down
        """
        self.verify(self.default_stats, "tester port not support '%s'" % self.flag)
        bond_port = self.create_bonded_device(MODE_TLB_BALANCE, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "down")

        try:
            slaves = {}
            slaves["active"] = [self.vf_ports[1], self.vf_ports[2]]
            slaves["inactive"] = [self.vf_ports[0]]

            self.verify_tlb_rx(self.vf_ports[3], bond_port, **slaves)
            self.verify_tlb_tx(self.vf_ports[3], bond_port, **slaves)
        finally:
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "up")

    def test_tlb_all_slaves_down(self):
        """
        Test Case22: Mode 5(TLB) Bring all slave links down
        """
        self.verify(self.default_stats, "tester port not support '%s'" % self.flag)
        bond_port = self.create_bonded_device(MODE_TLB_BALANCE, SOCKET_0)
        self.add_slave_to_bonding_device(
            bond_port, False, self.vf_ports[0], self.vf_ports[1], self.vf_ports[2]
        )
        self.dut.send_expect(
            "set portlist %d,%d" % (self.vf_ports[3], bond_port), "testpmd> "
        )
        self.start_port("all")
        self.dut.send_expect("start", "testpmd> ")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "down")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[1]), "down")
        self.admin_tester_port(self.tester.get_local_port(self.dut_ports[2]), "down")

        try:
            slaves = {}
            slaves["active"] = []
            slaves["inactive"] = [
                self.vf_ports[0],
                self.vf_ports[1],
                self.vf_ports[2],
            ]

            self.verify_tlb_rx(self.vf_ports[3], bond_port, **slaves)
            self.verify_tlb_tx(self.vf_ports[3], bond_port, **slaves)
        finally:
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[0]), "up")
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[1]), "up")
            self.admin_tester_port(self.tester.get_local_port(self.dut_ports[2]), "up")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.pmdout.quit()
        if self.running_case in ["test_bound_promisc_opt", "test_tlb_basic"]:
            self.dut.send_expect(
                "ip link set %s vf 0 trust off" % (self.dport_ifaces0), "# "
            )

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.dut.destroy_all_sriov_vfs()
        if self.default_stats:
            for port in self.dut_ports:
                tester_port = self.tester.get_local_port(port)
                tport_iface = self.tester.get_interface(tester_port)
                self.tester.send_expect(
                    "ethtool --set-priv-flags %s %s %s"
                    % (tport_iface, self.flag, self.default_stats),
                    "# ",
                )
