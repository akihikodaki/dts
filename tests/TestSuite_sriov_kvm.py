# BSD LICENSE
#
# Copyright(c) 2020 Intel Corporation. All rights reserved.
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
DPDK Test suite.


Test userland 10Gb PMD.

"""

import pdb
import random
import re
import time

from framework.pmd_output import PmdOutput
from framework.settings import PROTOCOL_PACKET_SIZE
from framework.test_case import TestCase
from framework.virt_common import VM

FRAME_SIZE_64 = 64
VM_CORES_MASK = "all"


class TestSriovKvm(TestCase):
    supported_vf_driver = ["pci-stub", "vfio-pci"]

    def set_up_all(self):
        # port_mirror_ref = {port_id: rule_id_list}
        # rule_id should be integer, and should be increased based on
        # the most rule_id when add a rule for a port successfully,
        # case should not be operate it directly
        # example:
        #          port_mirror_ref = {0: 1, 1: 3}
        self.port_mirror_ref = {}
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")

        self.vm0 = None
        self.vm1 = None

        self.vf_driver = self.get_suite_cfg()["vf_driver"]
        if self.vf_driver is None:
            self.vf_driver = "pci-stub"
        self.verify(self.vf_driver in self.supported_vf_driver, "Unspported vf driver")
        if self.vf_driver == "pci-stub":
            self.vf_assign_method = "pci-assign"
        else:
            self.vf_assign_method = "vfio-pci"
            self.dut.send_expect("modprobe vfio-pci", "#")
        self.setup_2vm_2vf_env_flag = 0
        self.setup_2vm_prerequisite_flag = 0
        self.vm0_testpmd = None
        self.vm1_testpmd = None
        self.setup_2vm_2vf_env()

    def set_up(self):

        self.setup_two_vm_common_prerequisite()

    def get_stats(self, dut, portid, rx_tx):
        """
        Get packets number from port statistic
        """

        stats = dut.testpmd.get_pmd_stats(portid)

        if rx_tx == "rx":
            stats_result = [stats["RX-packets"], stats["RX-missed"], stats["RX-bytes"]]
        elif rx_tx == "tx":
            stats_result = [stats["TX-packets"], stats["TX-errors"], stats["TX-bytes"]]
        else:
            return None

        return stats_result

    def parse_ether_ip(self, dut, dut_ports, dest_port, **ether_ip):
        """
        dut: which you want to send packet to
        dest_port: the port num must be the index of dut.get_ports()
        ether_ip:
            'ether':
                {
                    'dest_mac':False
                    'src_mac':"52:00:00:00:00:00"
                }
            'vlan':
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
        vlan = {}
        ip = {}
        udp = {}

        try:
            dut_dest_port = dut_ports[dest_port]
        except Exception as e:
            print(e)

        # using api get_local_port() to get the correct tester port.
        tester_port = self.tester.get_local_port(dut_dest_port)
        if not ether_ip.get("ether"):
            ether["dest_mac"] = PmdOutput(dut).get_port_mac(dut_dest_port)
            ether["src_mac"] = dut.tester.get_mac(tester_port)
        else:
            if not ether_ip["ether"].get("dest_mac"):
                ether["dest_mac"] = PmdOutput(dut).get_port_mac(dut_dest_port)
            else:
                ether["dest_mac"] = ether_ip["ether"]["dest_mac"]
            if not ether_ip["ether"].get("src_mac"):
                ether["src_mac"] = dut.tester.get_mac(tester_port)
            else:
                ether["src_mac"] = ether_ip["ether"]["src_mac"]

        if not ether_ip.get("vlan"):
            pass
        else:
            if not ether_ip["vlan"].get("vlan"):
                vlan["vlan"] = "1"
            else:
                vlan["vlan"] = ether_ip["vlan"]["vlan"]

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
        ret_ether_ip["vlan"] = vlan
        ret_ether_ip["ip"] = ip
        ret_ether_ip["udp"] = udp

        return ret_ether_ip

    def send_packet(
        self,
        dut,
        dut_ports,
        dest_port,
        src_port=False,
        frame_size=FRAME_SIZE_64,
        count=1,
        invert_verify=False,
        **ether_ip,
    ):
        """
        Send count packet to portid
        dut: which you want to send packet to
        dest_port: the port num must be the index of dut.get_ports()
        count: 1 or 2 or 3 or ... or 'MANY'
               if count is 'MANY', then set count=1000,
               send packets during 5 seconds.
        ether_ip:
            'ether':
                {
                    'dest_mac':False
                    'src_mac':"52:00:00:00:00:00"
                }
            'vlan':
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
                during = 20
                count = 1000 * 10
            else:
                raise e

        gp0rx_pkts, gp0rx_err, gp0rx_bytes = [
            int(_) for _ in self.get_stats(dut, dest_port, "rx")
        ]
        if not src_port:
            itf = self.tester.get_interface(
                self.dut.ports_map[self.dut_ports[dest_port]]
            )
        else:
            itf = src_port

        ret_ether_ip = self.parse_ether_ip(dut, dut_ports, dest_port, **ether_ip)

        pktlen = frame_size - 18
        padding = pktlen - 20

        start = time.time()
        while True:
            self.tester.scapy_foreground()
            self.tester.scapy_append('nutmac="%s"' % ret_ether_ip["ether"]["dest_mac"])
            self.tester.scapy_append('srcmac="%s"' % ret_ether_ip["ether"]["src_mac"])

            if ether_ip.get("vlan"):
                self.tester.scapy_append(
                    "vlanvalue=%d" % int(ret_ether_ip["vlan"]["vlan"])
                )
            self.tester.scapy_append('destip="%s"' % ret_ether_ip["ip"]["dest_ip"])
            self.tester.scapy_append('srcip="%s"' % ret_ether_ip["ip"]["src_ip"])
            self.tester.scapy_append("destport=%d" % ret_ether_ip["udp"]["dest_port"])
            self.tester.scapy_append("srcport=%d" % ret_ether_ip["udp"]["src_port"])
            if not ret_ether_ip.get("vlan"):
                send_cmd = (
                    "sendp([Ether(dst=nutmac, src=srcmac)/"
                    + "IP(dst=destip, src=srcip, len=%s)/" % pktlen
                    + "UDP(sport=srcport, dport=destport)/"
                    + 'Raw(load="\x50"*%s)], ' % padding
                    + 'iface="%s", count=%d)' % (itf, count)
                )
            else:
                send_cmd = (
                    "sendp([Ether(dst=nutmac, src=srcmac)/Dot1Q(vlan=vlanvalue)/"
                    + "IP(dst=destip, src=srcip, len=%s)/" % pktlen
                    + "UDP(sport=srcport, dport=destport)/"
                    + 'Raw(load="\x50"*%s)], iface="%s", count=%d)'
                    % (padding, itf, count)
                )
            self.tester.scapy_append(send_cmd)

            self.tester.scapy_execute()
            loop += 1

            now = time.time()
            if (now - start) >= during:
                break
        time.sleep(0.5)

        p0rx_pkts, p0rx_err, p0rx_bytes = [
            int(_) for _ in self.get_stats(dut, dest_port, "rx")
        ]

        p0rx_pkts -= gp0rx_pkts
        p0rx_bytes -= gp0rx_bytes

        if not invert_verify:
            self.verify(p0rx_pkts >= count * loop, "Data not received by port")
        else:
            self.verify(
                p0rx_pkts == 0 or p0rx_pkts < count * loop,
                "Data received by port, but should not.",
            )
        return count * loop

    def setup_2vm_2vf_env(self, driver="igb_uio"):
        self.used_dut_port = self.dut_ports[0]

        self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 2, driver=driver)
        self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]["vfs_port"]
        try:

            for port in self.sriov_vfs_port:
                port.bind_driver(self.vf_driver)

            time.sleep(1)

            vf0_prop = {"opt_host": self.sriov_vfs_port[0].pci}
            vf1_prop = {"opt_host": self.sriov_vfs_port[1].pci}

            for port_id in self.dut_ports:
                if port_id == self.used_dut_port:
                    continue
                port = self.dut.ports_info[port_id]["port"]
                port.bind_driver()

            if driver == "igb_uio":
                # start testpmd with the two VFs on the host
                self.host_testpmd = PmdOutput(self.dut)
                eal_param = "-a %s " % self.dut.ports_info[0]["pci"]
                self.host_testpmd.start_testpmd(
                    "1S/2C/2T", "--rxq=4 --txq=4", eal_param=eal_param
                )
                self.host_testpmd.execute_cmd("set fwd rxonly")
                self.host_testpmd.execute_cmd("start")

            # set up VM0 ENV
            self.vm0 = VM(self.dut, "vm0", "sriov_kvm")
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop)
            self.vm_dut_0 = self.vm0.start()
            if self.vm_dut_0 is None:
                raise Exception("Set up VM0 ENV failed!")

            # set up VM1 ENV
            self.vm1 = VM(self.dut, "vm1", "sriov_kvm")
            self.vm1.set_vm_device(driver=self.vf_assign_method, **vf1_prop)
            self.vm_dut_1 = self.vm1.start()
            if self.vm_dut_1 is None:
                raise Exception("Set up VM1 ENV failed!")

            self.setup_2vm_2vf_env_flag = 1
        except Exception as e:
            self.destroy_2vm_2vf_env()
            raise Exception(e)

    def destroy_2vm_2vf_env(self):
        if getattr(self, "vm0", None):
            self.vm0.stop()
            self.vm0 = None

        if getattr(self, "vm1", None):
            self.vm1.stop()
            self.vm1 = None

        if getattr(self, "host_testpmd", None):
            self.host_testpmd.execute_cmd("quit", "# ")
            self.host_testpmd = None

        self.dut.virt_exit()

        if getattr(self, "used_dut_port", None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            port = self.dut.ports_info[self.used_dut_port]["port"]
            port.bind_driver("igb_uio")
            self.used_dut_port = None

        for port_id in self.dut_ports:
            port = self.dut.ports_info[port_id]["port"]
            port.bind_driver("igb_uio")

        self.setup_2vm_2vf_env_flag = 0

    def transform_integer(self, value):
        try:
            value = int(value)
        except ValueError as e:
            raise Exception("Value not integer,but is " + type(value))
        return value

    def make_port_new_ruleid(self, port):
        port = self.transform_integer(port)
        if port not in list(self.port_mirror_ref.keys()):
            max_rule_id = 0
        else:
            rule_ids = sorted(self.port_mirror_ref[port])
            if rule_ids:
                max_rule_id = rule_ids[-1] + 1
            else:
                max_rule_id = 0
        return max_rule_id

    def add_port_ruleid(self, port, rule_id):
        port = self.transform_integer(port)
        rule_id = self.transform_integer(rule_id)

        if port not in list(self.port_mirror_ref.keys()):
            self.port_mirror_ref[port] = [rule_id]
        else:
            self.verify(
                rule_id not in self.port_mirror_ref[port],
                "Rule id [%d] has been repeated, please check!" % rule_id,
            )
            self.port_mirror_ref[port].append(rule_id)

    def remove_port_ruleid(self, port, rule_id):
        port = self.transform_integer(port)
        rule_id = self.transform_integer(rule_id)
        if port not in list(self.port_mirror_ref.keys()):
            pass
        else:
            if rule_id not in self.port_mirror_ref[port]:
                pass
            else:
                self.port_mirror_ref[port].remove(rule_id)
            if not self.port_mirror_ref[port]:
                self.port_mirror_ref.pop(port)

    def setup_two_vm_common_prerequisite(self, fwd0="rxonly", fwd1="mac"):

        if self.setup_2vm_prerequisite_flag == 1:
            self.vm0_testpmd.execute_cmd("stop")
            self.vm1_testpmd.execute_cmd("stop")
        else:
            if self.vm0_testpmd:
                self.vm0_testpmd.quit()
                self.vm0_testpmd = None
            if self.vm1_testpmd:
                self.vm1_testpmd.quit()
                self.vm1_testpmd = None
            self.vm0_dut_ports = self.vm_dut_0.get_ports("any")
            self.vm0_testpmd = PmdOutput(self.vm_dut_0)
            self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
            self.vm1_dut_ports = self.vm_dut_1.get_ports("any")
            self.vm1_testpmd = PmdOutput(self.vm_dut_1)
            self.vm1_testpmd.start_testpmd(VM_CORES_MASK)
            self.setup_2vm_prerequisite_flag = 1

        self.vm0_testpmd.execute_cmd("set fwd %s" % fwd0)
        self.vm0_testpmd.execute_cmd("set promisc all off")
        self.vm0_testpmd.execute_cmd("start")
        self.vm1_testpmd.execute_cmd("set fwd %s" % fwd1)
        self.vm1_testpmd.execute_cmd("set promisc all off")
        self.vm1_testpmd.execute_cmd("start")

    def destroy_two_vm_common_prerequisite(self):
        self.vm0_testpmd = None
        self.vm0_dut_ports = None

        self.vm0_testpmd = None
        self.vm1_dut_ports = None

        self.dut.virt_exit()

        self.setup_2vm_prerequisite_flag = 0

    def test_two_vms_intervm_communication(self):
        if self.setup_2vm_prerequisite_flag == 1:
            self.vm0_testpmd.execute_cmd("quit", "# ")
            self.vm1_testpmd.execute_cmd("quit", "# ")
        self.vm0_dut_ports = self.vm_dut_0.get_ports("any")
        self.vm1_dut_ports = self.vm_dut_1.get_ports("any")
        port_id_0 = 0
        packet_num = 10

        self.vm1_testpmd = PmdOutput(self.vm_dut_1)
        self.vm1_testpmd.start_testpmd(VM_CORES_MASK)
        vf1_mac = self.vm1_testpmd.get_port_mac(port_id_0)
        self.vm1_testpmd.execute_cmd("set fwd mac")
        self.vm1_testpmd.execute_cmd("set promisc all off")
        self.vm1_testpmd.execute_cmd("start")

        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK, "--eth-peer=0,%s" % vf1_mac)
        vf0_mac = self.vm0_testpmd.get_port_mac(port_id_0)
        self.vm0_testpmd.execute_cmd("set fwd mac")
        self.vm0_testpmd.execute_cmd("set promisc all off")
        self.vm0_testpmd.execute_cmd("start")

        # restart testpmd after this cases, because in this case have set some special cmd
        self.setup_2vm_prerequisite_flag = 0
        time.sleep(2)

        vm1_start_stats = self.vm1_testpmd.get_pmd_stats(port_id_0)
        self.send_packet(self.vm_dut_0, self.vm0_dut_ports, port_id_0, count=packet_num)
        vm1_end_stats = self.vm1_testpmd.get_pmd_stats(port_id_0)

        self.verify(
            vm1_end_stats["TX-packets"] - vm1_start_stats["TX-packets"] == packet_num,
            "VM1 transmit packets failed when sending packets to VM0",
        )

    def calculate_stats(self, start_stats, end_stats):
        ret_stats = {}
        for key in list(start_stats.keys()):
            try:
                start_stats[key] = int(start_stats[key])
                end_stats[key] = int(end_stats[key])
            except TypeError:
                ret_stats[key] = end_stats[key]
                continue
            ret_stats[key] = end_stats[key] - start_stats[key]
        return ret_stats

    def test_two_vms_add_multi_exact_mac_on_vf(self):
        port_id_0 = 0
        vf_num = 0
        packet_num = 10

        self.setup_2vm_prerequisite_flag = 0
        for vf_mac in ["00:11:22:33:44:55", "00:55:44:33:22:11"]:
            set_mac_cmd = "mac_addr add port %d vf %d %s"
            self.host_testpmd.execute_cmd(set_mac_cmd % (port_id_0, vf_num, vf_mac))

            vm0_start_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)
            ether_ip = {}
            ether_ip["ether"] = {"dest_mac": "%s" % vf_mac}
            self.send_packet(
                self.vm_dut_0,
                self.vm0_dut_ports,
                port_id_0,
                count=packet_num,
                **ether_ip,
            )
            vm0_end_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)

            vm0_ret_stats = self.calculate_stats(vm0_start_stats, vm0_end_stats)

            self.verify(
                self.vm0_testpmd.check_tx_bytes(
                    vm0_ret_stats["RX-packets"], packet_num
                ),
                "Add exact MAC %s failed btween VF0 and VF1" % vf_mac
                + "when add multi exact MAC address on VF!",
            )

    def test_two_vms_enalbe_or_disable_one_uta_mac_on_vf(self):
        self.verify(
            self.is_eth_series_nic(700) == False,
            "NIC is [%s], skip this case" % self.nic,
        )
        if self.is_eth_series_nic(700):
            self.dut.logger.warning("NIC is [%s], skip this case" % self.nic)
            return

        self.setup_2vm_prerequisite_flag = 0
        port_id_0 = 0
        vf_mac = "00:11:22:33:44:55"
        packet_num = 10

        self.host_testpmd.execute_cmd("set promisc %d on" % port_id_0)
        self.host_testpmd.execute_cmd("set port %d vf 0 rxmode ROPE on" % port_id_0)
        self.host_testpmd.execute_cmd("set port %d vf 1 rxmode ROPE off" % port_id_0)
        self.host_testpmd.execute_cmd("set port %d uta %s on" % (port_id_0, vf_mac))

        vm0_start_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)
        ether_ip = {}
        ether_ip["ether"] = {"dest_mac": "%s" % vf_mac}
        self.send_packet(
            self.vm_dut_0, self.vm0_dut_ports, port_id_0, count=packet_num, **ether_ip
        )
        vm0_end_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)

        vm0_ret_stats = self.calculate_stats(vm0_start_stats, vm0_end_stats)

        self.verify(
            self.vm0_testpmd.check_tx_bytes(vm0_ret_stats["RX-packets"], packet_num),
            "Enable one uta MAC failed between VM0 and VM1 "
            + "when enable or disable one uta MAC address on VF!",
        )

        self.host_testpmd.execute_cmd("set promisc %d off" % port_id_0)
        self.host_testpmd.execute_cmd("set port %d vf 0 rxmode ROPE off" % port_id_0)

        vm0_start_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)
        ether_ip = {}
        ether_ip["ether"] = {"dest_mac": "%s" % vf_mac}
        self.send_packet(
            self.vm_dut_0,
            self.vm0_dut_ports,
            port_id_0,
            count=packet_num,
            invert_verify=True,
            **ether_ip,
        )
        vm0_end_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)

        vm0_ret_stats = self.calculate_stats(vm0_start_stats, vm0_end_stats)

        self.verify(
            self.vm0_testpmd.check_tx_bytes(vm0_ret_stats["RX-packets"], 0),
            "Disable one uta MAC failed between VM0 and VM1 "
            + "when enable or disable one uta MAC address on VF!",
        )

    def test_two_vms_add_multi_uta_mac_on_vf(self):
        self.verify(
            not self.is_eth_series_nic(700),
            "NIC is [%s], skip this case" % self.nic,
        )
        if self.is_eth_series_nic(700):
            self.dut.logger.warning("NIC is [%s], skip this case" % self.nic)
            return

        port_id_0 = 0
        packet_num = 10

        self.setup_2vm_prerequisite_flag = 0
        for vf_mac in ["00:55:44:33:22:11", "00:55:44:33:22:66"]:
            self.host_testpmd.execute_cmd("set port %d uta %s on" % (port_id_0, vf_mac))
            self.host_testpmd.execute_cmd("set port %d uta %s on" % (port_id_0, vf_mac))

        for vf_mac in ["00:55:44:33:22:11", "00:55:44:33:22:66"]:
            vm0_start_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)
            ether_ip = {}
            ether_ip["ether"] = {"dest_mac": "%s" % vf_mac}
            self.send_packet(
                self.vm_dut_0,
                self.vm0_dut_ports,
                port_id_0,
                count=packet_num,
                **ether_ip,
            )
            vm0_end_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)

            vm0_ret_stats = self.calculate_stats(vm0_start_stats, vm0_end_stats)

            self.verify(
                self.vm0_testpmd.check_tx_bytes(
                    vm0_ret_stats["RX-packets"], packet_num
                ),
                "Add MULTI uta MAC %s failed between VM0 and VM1 " % vf_mac
                + "when add multi uta MAC address on VF!",
            )

    def test_two_vms_add_or_remove_uta_mac_on_vf(self):
        self.verify(
            not self.is_eth_series_nic(700),
            "NIC is [%s], skip this case" % self.nic,
        )
        if self.is_eth_series_nic(700):
            self.dut.logger.warning("NIC is [%s], skip this case" % self.nic)
            return

        self.setup_2vm_prerequisite_flag = 0
        port_id_0 = 0
        vf_mac = "00:55:44:33:22:11"
        packet_num = 10

        for switch in ["on", "off", "on"]:
            self.host_testpmd.execute_cmd(
                "set port %d uta %s %s" % (port_id_0, vf_mac, switch)
            )

            vm0_start_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)
            ether_ip = {}
            ether_ip["ether"] = {"dest_mac": "%s" % vf_mac}
            if switch == "on":
                self.send_packet(
                    self.vm_dut_0,
                    self.vm0_dut_ports,
                    port_id_0,
                    count=packet_num,
                    **ether_ip,
                )
            else:
                self.send_packet(
                    self.vm_dut_0,
                    self.vm0_dut_ports,
                    port_id_0,
                    count=packet_num,
                    invert_verify=True,
                    **ether_ip,
                )
            vm0_end_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)

            vm0_ret_stats = self.calculate_stats(vm0_start_stats, vm0_end_stats)

            if switch == "on":
                self.verify(
                    self.vm0_testpmd.check_tx_bytes(
                        vm0_ret_stats["RX-packets"], packet_num
                    ),
                    "Add MULTI uta MAC %s failed between VM0 and VM1 " % vf_mac
                    + "when add or remove multi uta MAC address on VF!",
                )
            else:
                self.verify(
                    self.vm0_testpmd.check_tx_bytes(vm0_ret_stats["RX-packets"], 0),
                    "Remove MULTI uta MAC %s failed between VM0 and VM1 " % vf_mac
                    + "when add or remove multi uta MAC address on VF!",
                )

    def test_two_vms_pause_rx_queues(self):
        self.verify(
            not self.is_eth_series_nic(700),
            "NIC is [%s], skip this case" % self.nic,
        )
        if self.is_eth_series_nic(700):
            self.dut.logger.warning("NIC is [%s], skip this case" % self.nic)
            return

        self.setup_2vm_prerequisite_flag = 0
        port_id_0 = 0
        packet_num = 10

        for switch in ["on", "off", "on"]:
            self.host_testpmd.execute_cmd(
                "set port %d vf 0 rx %s" % (port_id_0, switch)
            )

            vm0_start_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)
            if switch == "on":
                self.send_packet(
                    self.vm_dut_0, self.vm0_dut_ports, port_id_0, count=packet_num
                )
            else:
                self.send_packet(
                    self.vm_dut_0,
                    self.vm0_dut_ports,
                    port_id_0,
                    count=packet_num,
                    invert_verify=True,
                )
            vm0_end_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)

            vm0_ret_stats = self.calculate_stats(vm0_start_stats, vm0_end_stats)

            if switch == "on":
                self.verify(
                    self.vm0_testpmd.check_tx_bytes(
                        vm0_ret_stats["RX-packets"], packet_num
                    ),
                    "Enable RX queues failed between VM0 and VM1 "
                    + "when enable or pause RX queues on VF!",
                )
            else:
                self.verify(
                    self.vm0_testpmd.check_tx_bytes(vm0_ret_stats["RX-packets"], 0),
                    "Pause RX queues failed between VM0 and VM1 "
                    + "when enable or pause RX queues on VF!",
                )

    def test_two_vms_pause_tx_queuse(self):
        self.verify(
            not self.is_eth_series_nic(700),
            "NIC is [%s], skip this case" % self.nic,
        )
        if self.is_eth_series_nic(700):
            self.dut.logger.warning("NIC is [%s], skip this case" % self.nic)
            return

        self.vm0_testpmd.execute_cmd("stop")
        self.vm0_testpmd.execute_cmd("set fwd mac")
        self.vm0_testpmd.execute_cmd("start")

        port_id_0 = 0
        packet_num = 10

        self.setup_2vm_prerequisite_flag = 0
        for switch in ["on", "off", "on"]:
            self.host_testpmd.execute_cmd(
                "set port %d vf 0 tx %s" % (port_id_0, switch)
            )

            vm0_start_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)
            self.send_packet(
                self.vm_dut_0, self.vm0_dut_ports, port_id_0, count=packet_num
            )
            vm0_end_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)

            vm0_ret_stats = self.calculate_stats(vm0_start_stats, vm0_end_stats)

            if switch == "on":
                self.verify(
                    self.vm0_testpmd.check_tx_bytes(
                        vm0_ret_stats["TX-packets"], packet_num
                    ),
                    "Enable TX queues failed between VM0 and VM1 "
                    + "when enable or pause TX queues on VF!",
                )
            else:
                self.verify(
                    self.vm0_testpmd.check_tx_bytes(vm0_ret_stats["TX-packets"], 0),
                    "Pause TX queues failed between VM0 and VM1 "
                    + "when enable or pause TX queues on VF!",
                )

    def test_two_vms_prevent_rx_broadcast_on_vf(self):
        self.verify(
            not self.is_eth_series_nic(700),
            "NIC is [%s], skip this case" % self.nic,
        )
        if self.is_eth_series_nic(700):
            self.dut.logger.warning("NIC is [%s], skip this case" % self.nic)
            return

        port_id_0 = 0
        vf_mac = "FF:FF:FF:FF:FF:FF"
        packet_num = 10

        self.setup_2vm_prerequisite_flag = 0
        for switch in ["on", "off", "on"]:
            self.host_testpmd.execute_cmd(
                "set port %d vf 0 rxmode BAM %s" % (port_id_0, switch)
            )

            vm0_start_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)
            ether_ip = {}
            ether_ip["ether"] = {"dest_mac": "%s" % vf_mac}
            if switch == "on":
                self.send_packet(
                    self.vm_dut_0,
                    self.vm0_dut_ports,
                    port_id_0,
                    count=packet_num,
                    **ether_ip,
                )
            else:
                self.send_packet(
                    self.vm_dut_0,
                    self.vm0_dut_ports,
                    port_id_0,
                    count=packet_num,
                    invert_verify=True,
                    **ether_ip,
                )
            vm0_end_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)

            vm0_ret_stats = self.calculate_stats(vm0_start_stats, vm0_end_stats)

            if switch == "on":
                self.verify(
                    self.vm0_testpmd.check_tx_bytes(
                        vm0_ret_stats["RX-packets"], packet_num
                    ),
                    "Enable RX broadcast failed between VM0 and VM1 "
                    + "when enable or disable RX queues on VF!",
                )
            else:
                self.verify(
                    self.vm0_testpmd.check_tx_bytes(vm0_ret_stats["RX-packets"], 0),
                    "Disable RX broadcast failed between VM0 and VM1 "
                    + "when enable or pause TX queues on VF!",
                )

    def tear_down(self):
        port_id_0 = 0
        self.vm0_testpmd.execute_cmd("clear port stats all")
        self.vm1_testpmd.execute_cmd("clear port stats all")
        self.vm0_testpmd.execute_cmd("stop")
        self.vm1_testpmd.execute_cmd("stop")
        time.sleep(1)

    def tear_down_all(self):
        if self.setup_2vm_prerequisite_flag == 1:
            self.destroy_two_vm_common_prerequisite()
        if self.setup_2vm_2vf_env_flag == 1:
            self.destroy_2vm_2vf_env()
        if getattr(self, "vm0", None):
            self.vm0.stop()
        if getattr(self, "vm1", None):
            self.vm1.stop()

        self.dut.virt_exit()

        for port_id in self.dut_ports:
            self.dut.destroy_sriov_vfs_by_port(port_id)
