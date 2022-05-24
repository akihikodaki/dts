# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2017 Intel Corporation
#

import os
import re
import time

from framework.dut import Dut
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.test_case import TestCase


class TestMacsecForIxgbe(TestCase):
    def set_up_all(self):
        """
        Prerequisite steps for each test suite.
        """
        self.verify(
            self.nic in ["IXGBE_10G-82599_SFP"], "NIC Unsupported: " + str(self.nic)
        )
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.core_list = self.dut.get_core_list("1S/4C/1T")
        self.verify(
            len(self.core_list) >= 4, "There has not enought cores to test this suite"
        )
        self.session_sec = self.dut.new_session()
        self.pci_rx = self.dut.ports_info[self.dut_ports[1]]["pci"]
        self.pci_tx = self.dut.ports_info[self.dut_ports[0]]["pci"]
        self.mac0 = self.dut.get_mac_address(self.dut_ports[0])
        self.mac1 = self.dut.get_mac_address(self.dut_ports[1])

        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        else:
            cur_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            self.output_path = os.sep.join([cur_path, self.logger.log_path])
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()

    def set_up(self):
        """
        Run before each test case.
        """
        self.ol_flags = 1

    def start_testpmd_rx(self):
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list[0:2], ports=[self.pci_rx], prefix="rx"
        )
        app_name = self.dut.apps_name["test-pmd"]
        cmd_rx = app_name + eal_params + "-- -i --port-topology=chained"
        return self.dut.send_expect(cmd_rx, "testpmd", 120)

    def start_testpmd_tx(self):
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list[2:4], ports=[self.pci_tx], prefix="tx"
        )
        app_name = self.dut.apps_name["test-pmd"]
        cmd_tx = app_name + eal_params + "-- -i --port-topology=chained"
        return self.session_sec.send_expect(cmd_tx, "testpmd", 120)

    def start_testpmd_perf(self):
        eal_params = self.dut.create_eal_parameters(cores=self.core_list[0:2])
        app_name = self.dut.apps_name["test-pmd"]
        cmd = app_name + eal_params + "-- -i --port-topology=chained"
        self.dut.send_expect(cmd, "testpmd", 120)
        self.rx_set_macsec_offload("on", "on")
        self.dut.send_expect("set fwd mac", "testpmd>", 2)
        self.dut.send_expect("start", "testpmd>", 2)

    def show_xstats(self):
        time.sleep(0.1)
        self.session_sec.send_expect("stop", "testpmd>", 2)
        out_out = self.session_sec.send_expect("show port xstats 0", "testpmd>")
        out_pkts_encrypted = int(
            re.compile("out_pkts_encrypted:\s+(.*?)\s+?").findall(out_out, re.S)[0]
        )
        out_octets_encrypted = int(
            re.compile("out_octets_encrypted:\s+(.*?)\s+?").findall(out_out, re.S)[0]
        )
        out_pkts_protected = int(
            re.compile("out_pkts_protected:\s+(.*?)\s+?").findall(out_out, re.S)[0]
        )
        out_octets_protected = int(
            re.compile("out_octets_protected:\s+(.*?)\s+?").findall(out_out, re.S)[0]
        )
        tx_good_packets = int(
            re.compile("tx_good_packets:\s+(.*?)\s+?").findall(out_out, re.S)[0]
        )
        if self.ol_flags == 0:
            pkts_content = self.dut.get_session_output(timeout=2)

        self.dut.send_expect("stop", "testpmd>", 2)
        out_in = self.dut.send_expect("show port xstats 0", "testpmd>")
        rx_good_packets = int(
            re.compile("rx_good_packets:\s+(.*?)\s+?").findall(out_in, re.S)[0]
        )
        in_pkts_ok = int(re.compile("in_pkts_ok:\s+(.*?)\s+?").findall(out_in, re.S)[0])
        in_octets_decrypted = int(
            re.compile("in_octets_decrypted:\s+(.*?)\s+?").findall(out_in, re.S)[0]
        )
        in_octets_validated = int(
            re.compile("in_octets_validated:\s+(.*?)\s+?").findall(out_in, re.S)[0]
        )
        in_pkts_late = int(
            re.compile("in_pkts_late:\s+(.*?)\s+?").findall(out_in, re.S)[0]
        )
        in_pkts_notvalid = int(
            re.compile("in_pkts_notvalid:\s+(.*?)\s+?").findall(out_in, re.S)[0]
        )
        in_pkts_nosci = int(
            re.compile("in_pkts_nosci:\s+(.*?)\s+?").findall(out_in, re.S)[0]
        )
        in_pkts_notusingsa = int(
            re.compile("in_pkts_notusingsa:\s+(.*?)\s+?").findall(out_in, re.S)[0]
        )

        list_1 = [
            "out_pkts_encrypted",
            "out_octets_encrypted",
            "out_pkts_protected",
            "out_octets_protected",
            "tx_good_packets",
            "rx_good_packets",
            "in_pkts_ok",
            "in_octets_decrypted",
            "in_octets_validated",
            "in_pkts_late",
            "in_pkts_notvalid",
            "in_pkts_nosci",
            "in_pkts_notusingsa",
        ]
        list_2 = [
            out_pkts_encrypted,
            out_octets_encrypted,
            out_pkts_protected,
            out_octets_protected,
            tx_good_packets,
            rx_good_packets,
            in_pkts_ok,
            in_octets_decrypted,
            in_octets_validated,
            in_pkts_late,
            in_pkts_notvalid,
            in_pkts_nosci,
            in_pkts_notusingsa,
        ]
        result_dict = dict(list(zip(list_1, list_2)))
        print(result_dict)

        if self.ol_flags == 0:
            return result_dict, pkts_content
        return result_dict

    def clear_port_xstats(self):
        self.dut.send_expect("clear port xstats 0", "testpmd>")
        self.session_sec.send_expect("clear port xstats 0", "testpmd>")

    def rx_set_macsec_offload(self, encrypt_rx, replay_rx):
        # rx port
        self.dut.send_expect("port stop 0", "testpmd>", 2)
        self.dut.send_expect(
            "set macsec offload 0 on encrypt %s replay-protect %s"
            % (encrypt_rx, replay_rx),
            "testpmd>",
        )
        self.dut.send_expect("port start 0", "testpmd>", 2)

    def tx_set_macsec_offload(self, encrypt_tx, replay_tx):
        # tx port
        self.session_sec.send_expect("port stop 0", "testpmd>", 2)
        self.session_sec.send_expect(
            "set macsec offload 0 on encrypt %s replay-protect %s"
            % (encrypt_tx, replay_tx),
            "testpmd>",
        )
        self.session_sec.send_expect("port start 0", "testpmd>", 2)

    def rx_set_macsec_various_param(self, pi, idx, an, pn, key):
        # rx port
        self.dut.send_expect("set macsec sc rx 0 %s %s" % (self.mac0, pi), "testpmd>")
        self.dut.send_expect(
            "set macsec sa rx 0 %s %s %s %s" % (idx, an, pn, key), "testpmd>"
        )
        self.dut.send_expect("set macsec sc tx 0 %s %s" % (self.mac1, pi), "testpmd>")
        self.dut.send_expect(
            "set macsec sa tx 0 %s %s %s %s" % (idx, an, pn, key), "testpmd>"
        )
        self.dut.send_expect("set fwd rxonly", "testpmd>")
        self.dut.send_expect("set promisc all on", "testpmd>")
        if self.ol_flags == 0:
            self.dut.send_expect("set verbose 1", "testpmd>")
        self.dut.send_expect("start", "testpmd>", 2)

    def tx_set_macsec_various_param(self, pi, idx, an, pn, key):
        # tx port
        self.session_sec.send_expect(
            "set macsec sc tx 0 %s %s" % (self.mac0, pi), "testpmd>"
        )
        self.session_sec.send_expect(
            "set macsec sa tx 0 %s %s %s %s" % (idx, an, pn, key), "testpmd>"
        )
        self.session_sec.send_expect(
            "set macsec sc rx 0 %s %s" % (self.mac1, pi), "testpmd>"
        )
        self.session_sec.send_expect(
            "set macsec sa rx 0 %s %s %s %s" % (idx, an, pn, key), "testpmd>"
        )
        self.session_sec.send_expect("set fwd txonly", "testpmd>")
        self.session_sec.send_expect("start", "testpmd>", 2)

    def packets_receive_num(self):
        time.sleep(0.1)
        self.session_sec.send_expect("stop", "testpmd>", 2)
        self.dut.send_expect("stop", "testpmd>", 2)
        out = self.dut.send_expect("show port stats 0", "testpmd>")
        packet_number = re.compile("RX-packets:\s+(.*?)\s+?").findall(out, re.S)
        return packet_number

    def check_MACsec_pkts_receive(self):
        xstats = self.show_xstats()
        self.verify(
            xstats.get("out_pkts_protected") == 0
            and xstats.get("out_pkts_encrypted")
            == xstats.get("in_pkts_ok")
            == xstats.get("tx_good_packets")
            == xstats.get("rx_good_packets")
            and xstats.get("in_pkts_ok") != 0
            and xstats.get("out_octets_encrypted") == xstats.get("in_octets_decrypted")
            and xstats.get("out_octets_encrypted") != 0
            and xstats.get("out_octets_protected") == xstats.get("in_octets_validated")
            and xstats.get("out_octets_protected") != 0,
            "MACsec pkts receive failed",
        )

    def test_MACsec_pkts_tx_and_rx(self):
        """
        MACsec packets send and receive
        """
        self.start_testpmd_rx()
        self.rx_set_macsec_offload("on", "on")
        self.rx_set_macsec_various_param(0, 0, 0, 0, "00112200000000000000000000000000")
        self.start_testpmd_tx()
        self.tx_set_macsec_offload("on", "on")
        self.tx_set_macsec_various_param(0, 0, 0, 0, "00112200000000000000000000000000")
        self.check_MACsec_pkts_receive()

    def test_MACsec_encrypt_off_and_replay_protect_off(self):
        """
        encrypt on/off, replay-protect on/off
        """
        self.start_testpmd_rx()
        self.rx_set_macsec_offload("on", "on")
        self.rx_set_macsec_various_param(0, 0, 0, 0, "00112200000000000000000000000000")
        self.start_testpmd_tx()
        self.tx_set_macsec_offload("off", "on")
        self.tx_set_macsec_various_param(0, 0, 0, 0, "00112200000000000000000000000000")
        xstats = self.show_xstats()
        self.verify(
            xstats.get("out_pkts_encrypted") == 0
            and xstats.get("out_pkts_protected")
            == xstats.get("in_pkts_ok")
            == xstats.get("tx_good_packets")
            == xstats.get("rx_good_packets")
            and xstats.get("in_pkts_ok") != 0
            and xstats.get("out_octets_encrypted") == 0
            and xstats.get("in_octets_decrypted") == 0
            and xstats.get("out_octets_protected") == xstats.get("in_octets_validated")
            and xstats.get("out_pkts_protected") != 0,
            "failed",
        )
        self.session_sec.send_expect("quit", "#")
        self.dut.send_expect("quit", "#")

        self.start_testpmd_rx()
        self.rx_set_macsec_offload("on", "on")
        self.rx_set_macsec_various_param(0, 0, 0, 0, "00112200000000000000000000000000")
        self.start_testpmd_tx()
        self.tx_set_macsec_offload("on", "off")
        self.tx_set_macsec_various_param(0, 0, 0, 0, "00112200000000000000000000000000")
        self.check_MACsec_pkts_receive()

    def test_MACsec_tx_and_rx_with_various_param(self):
        """
        Set MACsec packets send and receive with various parameters, but keep the same value on both sides.
        """
        # rx side
        self.start_testpmd_rx()
        self.rx_set_macsec_offload("on", "on")
        # tx side
        self.start_testpmd_tx()
        self.tx_set_macsec_offload("on", "on")

        # subcase1:set various index on rx and tx port
        for i in [1, 2]:
            if i == 2:
                result = self.dut.send_expect(
                    "set macsec sa rx 0 %s 0 0 00112200000000000000000000000000" % i,
                    "testpmd>",
                )
                self.verify("invalid" in result, "set idx to 2 failed")
                break
            else:
                self.rx_set_macsec_various_param(
                    0, i, 0, 0, "00112200000000000000000000000000"
                )
                self.tx_set_macsec_various_param(
                    0, i, 0, 0, "00112200000000000000000000000000"
                )
                self.check_MACsec_pkts_receive()
                self.clear_port_xstats()

        # subcase2:set various an on rx and tx port
        for i in range(1, 5):
            if i == 4:
                result = self.dut.send_expect(
                    "set macsec sa rx 0 0 %s 0 00112200000000000000000000000000" % i,
                    "testpmd>",
                )
                self.verify("invalid" in result, "set an to 4 failed")
                break
            else:
                self.rx_set_macsec_various_param(
                    0, 0, i, 0, "00112200000000000000000000000000"
                )
                self.tx_set_macsec_various_param(
                    0, 0, i, 0, "00112200000000000000000000000000"
                )
                self.check_MACsec_pkts_receive()
                self.clear_port_xstats()
        self.session_sec.send_expect("quit", "#")
        self.dut.send_expect("quit", "#")

        # subcase3:set various pn on rx and tx port
        for i in [
            "0xffffffed",
            "0xffffffee",
            "0xffffffef",
            "0xfffffff0",
            "0xffffffec",
            "0x100000000",
        ]:
            # rx side
            self.start_testpmd_rx()
            self.rx_set_macsec_offload("on", "on")
            # tx side
            self.start_testpmd_tx()
            self.tx_set_macsec_offload("on", "on")
            if i == "0x100000000":
                result = self.dut.send_expect(
                    "set macsec sa rx 0 0 0 %s 00112200000000000000000000000000" % i,
                    "testpmd>",
                )
                self.verify("Bad arguments" in result, "set pn to 0x100000000 failed")
                break
            else:
                self.rx_set_macsec_various_param(
                    0, 0, 0, i, "00112200000000000000000000000000"
                )
                self.tx_set_macsec_various_param(
                    0, 0, 0, i, "00112200000000000000000000000000"
                )
                pkt_num = self.packets_receive_num()
                if i == "0xffffffec":
                    self.verify(int(pkt_num[0]) == 4, "Rx port can't receive four pkts")
                    self.clear_port_xstats()
                else:
                    self.verify(
                        int(pkt_num[0]) == 3, "Rx port can't receive three pkts"
                    )
                    self.session_sec.send_expect("quit", "#")
                    self.dut.send_expect("quit", "#")

        # subcase4:set various key on rx and tx port
        for i in [
            "00000000000000000000000000000000",
            "ffffffffffffffffffffffffffffffff",
        ]:
            self.rx_set_macsec_various_param(0, 0, 0, 0, i)
            self.tx_set_macsec_various_param(0, 0, 0, 0, i)
            self.check_MACsec_pkts_receive()
            self.clear_port_xstats()

        # subcase5:set various pi on rx and tx port
        for i in [1, "0xffff", "0x10000"]:
            if i == "0x10000":
                result = self.dut.send_expect(
                    "set macsec sc rx 0 %s %s" % (self.mac0, i), "testpmd>"
                )
                self.verify("Bad arguments" in result, "set pi to 0x10000 failed")
                break
            else:
                self.rx_set_macsec_various_param(
                    i, 0, 0, 0, "0112200000000000000000000000000"
                )
                self.tx_set_macsec_various_param(
                    i, 0, 0, 0, "0112200000000000000000000000000"
                )
                pkt_num = self.packets_receive_num()
                self.verify(int(pkt_num[0]) == 0, "MACsec pkts can't be received")

    def test_MACsec_pkts_send_and_normal_receive(self):
        """
        Disable MACsec offload on rx port,enable MACsec offload on tx port
        """
        self.ol_flags = 0
        # rx port
        self.start_testpmd_rx()
        self.dut.send_expect("port stop 0", "testpmd>", 2)
        self.dut.send_expect("set macsec offload 0 off", "testpmd>")
        self.dut.send_expect("port start 0", "testpmd>", 2)
        self.dut.send_expect("set fwd rxonly", "testpmd>")
        self.dut.send_expect("set promisc all on", "testpmd>")
        self.dut.send_expect("set verbose 1", "testpmd>")
        self.dut.send_expect("start", "testpmd>", 2)

        # tx port
        self.start_testpmd_tx()
        self.tx_set_macsec_offload("on", "on")
        self.tx_set_macsec_various_param(0, 0, 0, 0, "00112200000000000000000000000000")
        xstats, pkts_content = self.show_xstats()
        self.verify(
            "L2_ETHER" in pkts_content
            and "L3_IPV4" not in pkts_content
            and "L4_UDP" not in pkts_content,
            "The received packets are not encrypted",
        )
        self.verify(
            xstats.get("in_octets_decrypted") == 0
            and xstats.get("in_octets_validated") == 0,
            "Error:in_octets_decrypted and in_octets_validated increase",
        )

    def test_normal_pkts_send_and_MACsec_receive(self):
        """
        Enable MACsec offload on rx port,disable MACsec offload on tx port
        """
        # rx port
        self.ol_flags = 0
        self.start_testpmd_rx()
        self.rx_set_macsec_offload("on", "on")
        self.rx_set_macsec_various_param(0, 0, 0, 0, "00112200000000000000000000000000")

        # tx port
        self.start_testpmd_tx()
        self.session_sec.send_expect("port stop 0", "testpmd>", 2)
        self.session_sec.send_expect("set macsec offload 0 off", "testpmd>")
        self.session_sec.send_expect("port start 0", "testpmd>", 2)
        self.session_sec.send_expect("set fwd txonly", "testpmd>")
        self.session_sec.send_expect("start", "testpmd>", 2)

        xstats, pkts_content = self.show_xstats()
        self.verify(
            "L2_ETHER L3_IPV4 L4_UDP" in pkts_content,
            "The received packets are encrypted",
        )
        self.verify(
            xstats.get("in_octets_decrypted") == 0
            and xstats.get("out_pkts_encrypted") == 0,
            "Error:in_octets_decrypted and out_pkts_encrypted increase",
        )

    def test_MACsec_tx_and_rx_with_wrong_param(self):
        """
        MACsec packets send and receive with wrong parameters
        """
        # rx side
        self.start_testpmd_rx()
        self.rx_set_macsec_offload("on", "on")
        # tx side
        self.start_testpmd_tx()
        self.tx_set_macsec_offload("on", "on")

        # subcase1:set different pn on rx and tx port
        self.rx_set_macsec_various_param(0, 0, 0, 2, "00112200000000000000000000000000")
        self.tx_set_macsec_various_param(0, 0, 0, 0, "00112200000000000000000000000000")
        xstats = self.show_xstats()
        self.verify(
            xstats.get("out_pkts_encrypted")
            == xstats.get("in_pkts_ok") + xstats.get("in_pkts_late")
            and xstats.get("out_octets_encrypted") == xstats.get("in_octets_decrypted"),
            "subcase1:failed",
        )
        self.clear_port_xstats()
        # Rx port can receive the packets until the pn equals the pn of tx port
        self.rx_set_macsec_various_param(0, 0, 0, 2, "00112200000000000000000000000000")
        self.tx_set_macsec_various_param(0, 0, 0, 2, "00112200000000000000000000000000")
        self.check_MACsec_pkts_receive()
        self.clear_port_xstats()

        # subcase2:set different keys on rx and tx port
        self.rx_set_macsec_various_param(0, 0, 0, 0, "00000000000000000000000000000000")
        self.tx_set_macsec_various_param(0, 0, 0, 0, "00112200000000000000000000000000")
        xstats = self.show_xstats()
        self.verify(
            xstats.get("in_pkts_ok") == 0
            and xstats.get("out_pkts_encrypted") == xstats.get("in_pkts_notvalid")
            and xstats.get("out_octets_encrypted") == xstats.get("in_octets_decrypted"),
            "subcase2:failed",
        )
        pkt_num = self.packets_receive_num()
        self.verify(int(pkt_num[0]) == 0, "Rx port can't receive pkts")
        self.clear_port_xstats()

        # subcase3:set different pi on rx and tx port
        self.rx_set_macsec_various_param(1, 0, 0, 0, "0112200000000000000000000000000")
        self.tx_set_macsec_various_param(0, 0, 0, 0, "0112200000000000000000000000000")
        xstats = self.show_xstats()
        self.verify(
            xstats.get("in_pkts_ok") == 0
            and xstats.get("out_pkts_encrypted") == xstats.get("in_pkts_nosci")
            and xstats.get("out_octets_encrypted") == xstats.get("in_octets_decrypted"),
            "subcase3:failed",
        )
        self.clear_port_xstats()

        # subcase4:set different an on rx and tx port
        self.rx_set_macsec_various_param(0, 0, 0, 0, "00112200000000000000000000000000")
        self.tx_set_macsec_various_param(0, 0, 1, 0, "00112200000000000000000000000000")
        xstats = self.show_xstats()
        self.verify(
            xstats.get("in_pkts_ok") == 0
            and xstats.get("out_pkts_encrypted") == xstats.get("in_pkts_notusingsa")
            and xstats.get("out_octets_encrypted") == xstats.get("in_octets_decrypted"),
            "subcase4:failed",
        )
        self.clear_port_xstats()

        # subcase5:set different index on rx and tx port
        self.rx_set_macsec_various_param(0, 0, 0, 0, "00112200000000000000000000000000")
        self.tx_set_macsec_various_param(0, 1, 0, 0, "00112200000000000000000000000000")
        xstats = self.show_xstats()
        self.verify(
            xstats.get("out_pkts_encrypted") == xstats.get("in_pkts_ok")
            and xstats.get("out_octets_encrypted") == xstats.get("in_octets_decrypted"),
            "subcase5:failed",
        )

    def test_packet_length(self):
        """
        On IXIA side, start IXIA port6 transmit, start the IXIA capture.
        View the IXIA port5 captured packet, the protocol is MACsec, the EtherType
        is 0x88E5, and the packet length is 96bytes, while the normal packet length
        is 64bytes.
        """
        self.tester_itf_0 = self.tester.get_interface(self.dut_ports[0])
        self.tester_itf_1 = self.tester.get_interface(self.dut_ports[1])
        self.start_testpmd_perf()
        # start tcpdump
        self.tester.send_expect("rm -rf ./tcpdump_test.cap", "#")
        self.tester.send_expect(
            "tcpdump -i %s ether src %s -w ./tcpdump_test.cap 2> /dev/null& "
            % (self.tester_itf_0, self.mac0),
            "#",
        )
        p = Packet()
        pkt = 'Ether(dst="%s", src="02:00:00:00:00:01")/IP()/UDP()/("X"*22)' % self.mac1
        p.append_pkt(pkt)
        p.send_pkt(self.tester, tx_port=self.tester_itf_1, count=10, timeout=3)
        # get tcpdump package
        self.tester.send_expect("killall tcpdump", "#")
        out = self.tester.send_expect(
            "tcpdump -nn -e -v -r ./tcpdump_test.cap", "#", 120
        )
        self.verify(
            "length 96" in out and "0x88e5" in out,
            "the EtherType isn't 0x88E5, and the packet length isn't 96bytes",
        )

    def test_perf_Tx_linerate(self):
        """
        performance test
        """
        self.table_header = ["Frame Size", "Mpps", "% linerate"]
        self.result_table_create(self.table_header)
        txPort = self.tester.get_local_port(self.dut_ports[1])
        rxPort = self.tester.get_local_port(self.dut_ports[0])
        self.start_testpmd_perf()
        # prepare traffic generator input
        flow = (
            'Ether(dst="%s", src="02:00:00:00:00:01")/IP()/UDP()/("X"*22)' % self.mac1
        )
        pcap = os.sep.join([self.output_path, "test.pcap"])
        self.tester.scapy_append('wrpcap("%s", [%s])' % (pcap, flow))
        self.tester.scapy_execute()
        tgenInput = []
        pcap = os.sep.join([self.output_path, "test.pcap"])
        tgenInput.append((txPort, rxPort, pcap))

        # clear streams before add new streams
        self.tester.pktgen.clear_streams()
        # run packet generator
        streams = self.pktgen_helper.prepare_stream_from_tginput(
            tgenInput, 100, None, self.tester.pktgen
        )
        _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)
        self.verify(pps > 0, "No traffic detected")
        pps /= 1000000.0
        rate = (pps * 100) / self.wirespeed(self.nic, 96, 1)
        self.result_table_add([96, pps, rate])
        self.result_table_print()
        self.verify(rate >= 96, "performance test failed")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.session_sec.send_expect("quit", "#")
        self.dut.send_expect("quit", "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.dut.close_session(self.session_sec)
