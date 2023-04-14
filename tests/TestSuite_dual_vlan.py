# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2015 Intel Corporation
#

"""
DPDK Test suite.

Test the support of Dual VLAN Offload Features by Poll Mode Drivers.

"""

import random
import re
import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestDualVlan(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.

        Vlan Prerequisites
        """
        global dutRxPortId
        global dutTxPortId

        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])

        cores = self.dut.get_core_list("1S/2C/2T")
        coreMask = utils.create_mask(cores)
        valports = [_ for _ in self.dut_ports if self.tester.get_local_port(_) != -1]
        portMask = utils.create_mask(valports[:2])
        dutRxPortId = valports[0]
        dutTxPortId = valports[1]

        self.pmdout = PmdOutput(self.dut)
        self.pmdout.start_testpmd(
            "Default", "--portmask=%s" % portMask, socket=self.ports_socket
        )

        # Get the firmware version information
        try:
            self.fwversion, _, _ = self.pmdout.get_firmware_version(
                self.dut_ports[0]
            ).split()
        except ValueError:
            # nic IXGBE, IGC
            self.fwversion = self.pmdout.get_firmware_version(self.dut_ports[0]).split()

        if self.nic in [
            "I40E_10G-SFP_XL710",
            "I40E_40G-QSFP_A",
            "I40E_40G-QSFP_B",
            "I40E_25G-25G_SFP28",
            "I40E_10G-SFP_X722",
            "I40E_10G-10G_BASE_T_BC",
            "I40E_10G-10G_BASE_T_X722",
        ]:
            self.dut.send_expect("vlan set filter on all", "testpmd> ")
            self.dut.send_expect("set promisc all off", "testpmd> ")

        out = self.dut.send_expect("set fwd mac", "testpmd> ")
        self.verify("Set mac packet forwarding mode" in out, "set fwd mac error")
        out = self.dut.send_expect("start", "testpmd> ", 120)

        # Vlan id
        self.txvlanId_id = 3
        self.outvlanId_id = 1
        self.invlanId_id = 2

        if self.kdriver == "i40e" and self.fwversion >= "8.40":
            self.config_i40e_firmware_vlan()
        else:
            self.config_original()

    def config_original(self):
        self.allResult = {
            "TX+OUTER+INNER": (self.txvlanId_id, self.outvlanId_id, self.invlanId_id),
            "TX+INNER": (self.txvlanId_id, self.invlanId_id),
            "TX+OUTER": (self.txvlanId_id, self.outvlanId_id),
            "OUTER+INNER": (self.outvlanId_id, self.invlanId_id),
            "INNER": (self.invlanId_id,),
            "OUTER": (self.outvlanId_id,),
            "NONE": ("No",),
        }

        self.stripCase = 0x1
        self.filterCase = 0x2
        self.qinqCase = 0x4
        self.txCase = 0x8

        self.vlanCaseDef = [
            0,
            self.stripCase,
            self.filterCase,
            self.filterCase | self.stripCase,
            self.qinqCase,
            self.qinqCase | self.stripCase,
            self.qinqCase | self.filterCase,
            self.qinqCase | self.filterCase | self.stripCase,
            self.txCase,
            self.txCase | self.stripCase,
            self.txCase | self.filterCase,
            self.txCase | self.filterCase | self.stripCase,
            self.txCase | self.qinqCase,
            self.txCase | self.qinqCase | self.stripCase,
            self.txCase | self.qinqCase | self.filterCase,
            self.txCase | self.qinqCase | self.filterCase | self.stripCase,
        ]

        self.vlanCase = [
            "OUTER+INNER",
            "INNER",
            ("OUTER+INNER", "NONE"),
            ("INNER", "NONE"),
            "OUTER+INNER",
            "OUTER",
            ("NONE", "OUTER+INNER"),
            ("NONE", "OUTER"),
            "TX+OUTER+INNER",
            "TX+INNER",
            ("TX+OUTER+INNER", "NONE"),
            ("TX+INNER", "NONE"),
            "TX+OUTER+INNER",
            "TX+OUTER",
            ("NONE", "TX+OUTER+INNER"),
            ("NONE", "TX+OUTER"),
        ]

    def config_i40e_firmware_vlan(self):
        self.allResult = {
            "TX+OUTER+INNER": (self.txvlanId_id, self.outvlanId_id, self.invlanId_id),
            "TX+INNER": (self.txvlanId_id, self.invlanId_id),
            "TX+OUTER": (self.txvlanId_id, self.outvlanId_id),
            "OUTER+INNER": (self.outvlanId_id, self.invlanId_id),
            "INNER": (self.invlanId_id,),
            "OUTER": (self.outvlanId_id,),
            "NONE": ("No",),
        }

        self.stripCase = 0x1
        self.filterCase = 0x2
        self.qinqCase = 0x4
        self.txCase = 0x8

        self.vlanCaseDef = [
            0,
            self.stripCase,
            self.filterCase | self.qinqCase,
            self.filterCase | self.qinqCase | self.stripCase,
            self.qinqCase,
            self.qinqCase | self.stripCase,
            self.qinqCase | self.filterCase,
            self.qinqCase | self.filterCase | self.stripCase,
            self.txCase,
            self.txCase | self.stripCase,
            self.txCase | self.filterCase | self.qinqCase,
            self.txCase | self.filterCase | self.qinqCase | self.stripCase,
            self.txCase | self.qinqCase,
            self.txCase | self.qinqCase | self.stripCase,
            self.txCase | self.qinqCase | self.filterCase,
            self.txCase | self.qinqCase | self.filterCase | self.stripCase,
        ]

        self.vlanCase = [
            "OUTER+INNER",
            "INNER",
            ("OUTER+INNER", "NONE"),
            ("OUTER", "NONE"),
            "OUTER+INNER",
            "OUTER",
            ("OUTER+INNER", "NONE"),
            ("OUTER", "NONE"),
            "TX+OUTER+INNER",
            "TX+INNER",
            ("TX+OUTER+INNER", "NONE"),
            ("TX+OUTER", "NONE"),
            "TX+OUTER+INNER",
            "TX+OUTER",
            ("TX+OUTER+INNER", "NONE"),
            ("TX+OUTER", "NONE"),
        ]

    def start_tcpdump(self, rxItf):

        self.tester.send_expect("rm -rf ./getPackageByTcpdump.cap", "#")
        self.tester.send_expect(
            "tcpdump -i %s -w ./getPackageByTcpdump.cap 2> /dev/null& " % rxItf, "#"
        )

    def get_tcpdump_package(self):
        self.tester.send_expect("killall tcpdump", "#")
        self.tester.send_expect("wait", "#")
        return self.tester.send_expect(
            "tcpdump -nn -e -v -r ./getPackageByTcpdump.cap", "#"
        )

    def vlan_send_packet(self, *vid):
        """
        Send packet to portid
        """
        txPort = self.tester.get_local_port(dutRxPortId)
        rxPort = self.tester.get_local_port(dutTxPortId)

        txItf = self.tester.get_interface(txPort)
        rxItf = self.tester.get_interface(rxPort)
        mac = self.dut.get_mac_address(dutRxPortId)

        self.start_tcpdump(rxItf)
        vlanString = 'sendp([Ether(dst="%s")/' % mac
        for i in range(len(vid)):
            vlanString += "Dot1Q(id=0x8100,vlan=%s)/" % vid[i]
        vlanString += 'IP(len=46)],iface="%s", count=4)' % txItf

        self.tester.scapy_append(vlanString)
        # check link status before send pkg
        self.pmdout.wait_link_status_up(self.dut_ports[0])
        self.tester.scapy_execute()

    def mode_config(self, **modeName):
        """
        Set up the VLAN mode.
        """

        for mode in modeName:
            if self.nic in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_40G-QSFP_B",
                "I40E_25G-25G_SFP28",
                "I40E_10G-SFP_X722",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_10G-10G_BASE_T_X722",
            ]:
                # Intel® Ethernet 700 Series NIC vlan filter can't close, if want close need remove rx_vlan
                if mode == "filter":
                    if modeName[mode] == "off":
                        self.dut.send_expect("vlan set filter off all", "testpmd> ")
                        continue
                    else:
                        self.dut.send_expect("vlan set filter on all", "testpmd> ")
                        continue

            if mode == "stripq":
                self.dut.send_expect(
                    "vlan set %s %s %s,0" % (mode, modeName[mode], dutRxPortId),
                    "testpmd> ",
                )
            else:
                self.dut.send_expect(
                    "vlan set %s %s %s" % (mode, modeName[mode], dutRxPortId),
                    "testpmd> ",
                )

        out = self.dut.send_expect("show port info %s" % dutRxPortId, "testpmd> ")
        for mode in modeName:
            if self.nic in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_40G-QSFP_B",
                "I40E_25G-25G_SFP28",
                "I40E_10G-SFP_X722",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_10G-10G_BASE_T_X722",
            ]:
                # Intel® Ethernet 700 Series NIC vlan filter can't close, if want close need remove rx_vlan
                if mode == "filter":
                    if modeName[mode] == "off":
                        self.dut.send_expect("vlan set filter off all", "testpmd> ")
                        continue
                    else:
                        self.dut.send_expect("vlan set filter on all", "testpmd> ")
                        continue

            if mode == "extend":
                self.verify(
                    "extend %s" % modeName[mode] in out, "%s setting error" % mode
                )
                continue
            elif mode == "stripq":
                continue
            else:
                self.verify(
                    "%s %s" % (mode, modeName[mode]) in out, "%s setting error" % mode
                )

    def multimode_test(self, caseIndex):
        """
        Setup Strip/Filter/Extend/Insert enable/disable for synthetic test.
        """
        caseDef = self.vlanCaseDef[caseIndex]
        temp = []

        temp.append("on") if (caseDef & self.stripCase) != 0 else temp.append("off")
        temp.append("on") if (caseDef & self.filterCase) != 0 else temp.append("off")
        temp.append("on") if (caseDef & self.qinqCase) != 0 else temp.append("off")
        if (self.nic in ["cavium_a063", "cavium_a064"]) and temp[2] == "on":
            ## Skip QinQ for cavium devices as it is not supported.
            return
        self.mode_config(strip=temp[0], filter=temp[1], extend=temp[2])

        if (caseDef & self.txCase) != 0:
            self.dut.send_expect("stop", "testpmd> ")
            self.dut.send_expect("port stop all", "testpmd> ")
            self.dut.send_expect(
                "tx_vlan set %s %s" % (dutTxPortId, self.txvlanId_id), "testpmd> "
            )
            self.dut.send_expect("port start all", "testpmd> ")
            self.dut.send_expect("start", "testpmd> ")

        configMode = "Strip %s, filter %s 0x1, extend %s, insert %s" % (
            temp[0],
            temp[1],
            temp[2],
            "on" if (caseDef & self.txCase) != 0 else "off",
        )

        if (caseDef & self.filterCase) != 0:
            self.dut.send_expect(
                "rx_vlan add %s %s" % (self.outvlanId_id, dutRxPortId), "testpmd> "
            )
            self.vlan_send_packet(self.outvlanId_id, self.invlanId_id)
            self.check_result(self.vlanCase[caseIndex][0], configMode + " result Error")
            self.dut.send_expect(
                "rx_vlan rm %s %s" % (self.outvlanId_id, dutRxPortId), "testpmd> "
            )
            self.dut.send_expect(
                "rx_vlan add %s %s" % (self.invlanId_id, dutRxPortId), "testpmd> "
            )
            self.vlan_send_packet(self.outvlanId_id, self.invlanId_id)
            self.check_result(self.vlanCase[caseIndex][1], configMode + " result Error")
            self.dut.send_expect(
                "rx_vlan rm %s %s" % (self.invlanId_id, dutRxPortId), "testpmd> "
            )
            if (caseDef & self.txCase) != 0:
                self.dut.send_expect("stop", "testpmd> ")
                self.dut.send_expect("port stop all", "testpmd> ")
                self.dut.send_expect("tx_vlan reset %s" % dutTxPortId, "testpmd> ")
                self.dut.send_expect("port start all", "testpmd> ")
                self.dut.send_expect("start", "testpmd> ")

        else:
            self.dut.send_expect(
                "rx_vlan add %s %s" % (self.invlanId_id, dutRxPortId), "testpmd> "
            )
            self.dut.send_expect(
                "rx_vlan add %s %s" % (self.outvlanId_id, dutRxPortId), "testpmd> "
            )
            self.vlan_send_packet(self.outvlanId_id, self.invlanId_id)
            self.check_result(self.vlanCase[caseIndex], configMode + " result Error")
            if (caseDef & self.txCase) != 0:
                self.dut.send_expect("stop", "testpmd> ")
                self.dut.send_expect("port stop all", "testpmd> ")
                self.dut.send_expect("tx_vlan reset %s" % dutTxPortId, "testpmd> ")
                self.dut.send_expect("port start all", "testpmd> ")
                self.dut.send_expect("start", "testpmd> ")
            self.dut.send_expect(
                "rx_vlan rm %s %s" % (self.invlanId_id, dutRxPortId), "testpmd> "
            )
            self.dut.send_expect(
                "rx_vlan rm %s %s" % (self.outvlanId_id, dutRxPortId), "testpmd> "
            )

    def check_result(self, resultKey, errorString):
        """
        Check results of synthetic test.
        """
        print(("vlan flage config:%s" % errorString))
        out = self.get_tcpdump_package()
        if self.allResult[resultKey][0] == "No":
            self.verify("vlan" not in out, errorString)
        else:
            resultList = []
            for i in range(len(self.allResult[resultKey]) - 1):
                resultList.append("vlan %s" % self.allResult[resultKey][i])
            resultList.append(
                "vlan %s"
                % self.allResult[resultKey][len(self.allResult[resultKey]) - 1]
            )
            for line in resultList:
                self.verify(line in out, "receive packet is wrong:%s" % out)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_vlan_filter_config(self):
        """
        Enable/Disable VLAN packets filtering
        """
        self.mode_config(filter="on")
        self.mode_config(strip="off")
        # Because the kernel forces enable Qinq and cannot be closed,
        # the dpdk can only add 'extend on' to make the VLAN filter work normally.
        if self.kdriver == "i40e" and self.fwversion >= "8.40":
            self.mode_config(extend="on")
            self.dut.send_expect(
                "rx_vlan rm %s %s" % (self.outvlanId_id, dutRxPortId), "testpmd> "
            )
        else:
            self.mode_config(extend="off")

        self.vlan_send_packet(self.outvlanId_id)
        out = self.get_tcpdump_package()
        print(out)
        self.verify(
            out is not None and "vlan %s" % self.outvlanId_id not in out,
            "Vlan filter enable error: " + out,
        )
        self.logger.debug(self.nic)
        if self.nic not in [
            "ICE_25G-E810C_SFP",
            "ICE_100G-E810C_QSFP",
            "I40E_10G-SFP_XL710",
            "I40E_40G-QSFP_A",
            "I40E_40G-QSFP_B",
            "I40E_25G-25G_SFP28",
            "I40E_10G-SFP_X722",
            "I40E_10G-10G_BASE_T_BC",
            "I40E_10G-10G_BASE_T_X722",
        ]:
            self.mode_config(filter="off")
            self.vlan_send_packet(self.outvlanId_id)
            out = self.get_tcpdump_package()
            self.verify(
                "vlan %s" % self.outvlanId_id in out,
                "Vlan filter disable error: " + out,
            )
        else:
            self.dut.send_expect(
                "rx_vlan add %s %s" % (self.outvlanId_id, dutRxPortId), "testpmd> "
            )
            self.vlan_send_packet(self.outvlanId_id)
            out = self.get_tcpdump_package()
            self.verify(
                "vlan %s" % self.outvlanId_id in out,
                "Vlan filter disable error: " + out,
            )
            self.dut.send_expect(
                "rx_vlan rm %s %s" % (self.outvlanId_id, dutRxPortId), "testpmd> "
            )

    def test_vlan_filter_table(self):
        """
        Add/Remove VLAN Tag Identifier pass VLAN filtering
        """

        self.mode_config(filter="on")
        self.mode_config(strip="off")
        # Because the kernel forces enable Qinq and cannot be closed,
        # the dpdk can only add 'extend on' to make the VLAN filter work normally.
        if self.kdriver == "i40e" and self.fwversion >= "8.40":
            self.mode_config(extend="on")
        else:
            self.mode_config(extend="off")
        self.dut.send_expect(
            "rx_vlan add %s %s" % (self.outvlanId_id, dutRxPortId), "testpmd> "
        )
        self.vlan_send_packet(self.outvlanId_id)
        out = self.get_tcpdump_package()
        self.verify(
            "vlan %s" % self.outvlanId_id in out,
            "vlan filter table enable error: " + out,
        )

        self.dut.send_expect(
            "rx_vlan rm %s %s" % (self.outvlanId_id, dutRxPortId), "testpmd> "
        )
        self.vlan_send_packet(self.outvlanId_id)
        out = self.get_tcpdump_package()
        self.verify(
            out is not None and "vlan %s" % self.outvlanId_id not in out,
            "vlan filter table disable error: " + out,
        )

    def test_vlan_strip_config(self):
        """
        Enable/Disable VLAN packets striping
        """

        self.mode_config(filter="off")
        self.mode_config(extend="off")
        self.mode_config(strip="on")
        if self.nic in [
            "ICE_25G-E810C_SFP",
            "ICE_100G-E810C_QSFP",
            "I40E_10G-SFP_XL710",
            "I40E_40G-QSFP_A",
            "I40E_40G-QSFP_B",
            "I40E_25G-25G_SFP28",
            "I40E_10G-SFP_X722",
            "I40E_10G-10G_BASE_T_BC",
            "I40E_10G-10G_BASE_T_X722",
        ]:
            self.dut.send_expect(
                "rx_vlan add %s %s" % (self.outvlanId_id, dutRxPortId), "testpmd> "
            )
        self.vlan_send_packet(self.outvlanId_id)
        out = self.get_tcpdump_package()
        self.verify(
            "vlan %s" % self.outvlanId_id not in out, "Vlan strip enable error: " + out
        )

        self.mode_config(strip="off")
        self.vlan_send_packet(self.outvlanId_id)
        out = self.get_tcpdump_package()
        self.verify(
            "vlan %s" % self.outvlanId_id in out, "Vlan strip disable error: " + out
        )
        if self.nic in [
            "ICE_25G-E810C_SFP",
            "ICE_100G-E810C_QSFP",
            "I40E_10G-SFP_XL710",
            "I40E_40G-QSFP_A",
            "I40E_40G-QSFP_B",
            "I40E_25G-25G_SFP28",
            "I40E_10G-SFP_X722",
            "I40E_10G-10G_BASE_T_BC",
            "I40E_10G-10G_BASE_T_X722",
        ]:
            self.dut.send_expect(
                "rx_vlan rm %s %s" % (self.outvlanId_id, dutRxPortId), "testpmd> "
            )

    def test_vlan_stripq_config(self):
        """
        Enable/Disable VLAN packets strip on queue
        """
        self.mode_config(filter="off")
        self.mode_config(extend="off")
        self.mode_config(strip="off")
        self.mode_config(stripq="off")
        self.vlan_send_packet(self.outvlanId_id)
        out = self.get_tcpdump_package()
        self.verify(
            "vlan %s" % self.outvlanId_id in out,
            "vlan strip queue disable error : " + out,
        )
        # if self.nic in ["I40E_10G-SFP_XL710", "I40E_40G-QSFP_A", "I40E_40G-QSFP_B"]:
        self.mode_config(strip="on")
        self.mode_config(stripq="on")
        self.vlan_send_packet(self.outvlanId_id)
        out = self.get_tcpdump_package()
        self.verify(
            "vlan %s" % self.outvlanId_id not in out, "vlan strip enable error: " + out
        )

        self.mode_config(stripq="off")
        self.vlan_send_packet(self.outvlanId_id)
        out = self.get_tcpdump_package()
        self.verify(
            "vlan %s" % self.outvlanId_id in out,
            "vlan strip queue disable error: " + out,
        )

    def test_vlan_insert_config(self):
        """
        Enable/Disable VLAN packets inserting
        """
        self.mode_config(filter="off")
        self.mode_config(extend="off")

        # IGB_1G-82574L need to set CTRL.VME for vlan insert
        if self.nic == "IGB_1G-82574L":
            self.dut.send_expect("vlan set strip on %s" % dutTxPortId, "testpmd> ")

        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop all", "testpmd> ")
        self.dut.send_expect(
            "tx_vlan set %s %s" % (dutTxPortId, self.txvlanId_id), "testpmd> "
        )
        self.dut.send_expect("port start all", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        self.vlan_send_packet()
        out = self.get_tcpdump_package()
        self.verify(
            "vlan %s" % self.txvlanId_id in out, "vlan insert enable error: " + out
        )

        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop all", "testpmd> ")
        self.dut.send_expect("tx_vlan reset %s" % dutTxPortId, "testpmd> ")
        self.dut.send_expect("port start all", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        self.vlan_send_packet()
        out = self.get_tcpdump_package()
        self.verify(
            "vlan %s" % self.txvlanId_id not in out, "vlan insert disable error: " + out
        )

    def test_vlan_tpid_config(self):
        """
        Configure receive port inner VLAN TPID
        """
        self.verify(
            self.nic
            not in [
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
                "I40E_40G-QSFP_B",
                "IGB_1G-82574L",
                "I40E_10G-10G_BASE_T_BC",
            ],
            "%s NIC not support tcpid " % self.nic,
        )

        self.mode_config(filter="on", strip="on", extend="on")
        # i40e set VLAN id
        self.dut.send_expect(
            "rx_vlan add %s %s" % (self.outvlanId_id, dutRxPortId),
            "testpmd> ",
        )
        # nic only support inner model, except Intel® Ethernet 700 Series nic
        self.dut.send_expect("vlan set inner tpid 0x1234 %s" % dutRxPortId, "testpmd> ")
        self.vlan_send_packet(self.outvlanId_id, self.invlanId_id)

        out = self.get_tcpdump_package()
        self.verify("0x8100" in out, "tpid is error: " + out)
        self.verify(
            "vlan %s" % self.outvlanId_id in out, "vlan tpid disable error: " + out
        )
        self.verify(
            "vlan %s" % self.invlanId_id in out, "vlan tpid disable error: " + out
        )

        self.dut.send_expect("vlan set inner tpid 0x8100 %s" % dutRxPortId, "testpmd> ")
        self.vlan_send_packet(self.outvlanId_id, self.invlanId_id)

        out = self.get_tcpdump_package()
        # Because the kernel forces enable Qinq and cannot be closed,
        # the dpdk can only add 'extend on' to make the VLAN filter work normally.
        # The kernel driver uses the outer VLAN filter, and the DPDK synchronously modifies,
        # DPDK filter outer VLAN when firmware >= 8.4, the test result check strip inner.
        if self.kdriver == "i40e" and self.fwversion >= "8.40":
            self.verify("0x8100" in out, "tpid is error: " + out)
            self.verify(
                out is not None and f"vlan {self.invlanId_id}" not in out,
                "vlane tpid enable error: " + out,
            )
        else:
            self.verify(
                out is not None and "vlan" not in out, "vlane tpid enable error: " + out
            )

    def test_vlan_synthetic_test(self):
        """
        VLAN synthetic test.
        """
        self.verify(
            self.nic != "IGB_1G-82574L", "sorry, dual vlan cannot support this self.nic"
        )
        for i in range(len(self.vlanCase)):
            self.multimode_test(i)

    def test_vlan_random_test(self):
        """
        VLAN random test.
        """
        self.verify(
            self.nic != "IGB_1G-82574L", "sorry, dual vlan cannot support this self.nic"
        )
        for _ in range(30):
            rand = random.randint(0, 15)
            self.multimode_test(rand)

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
        pass
