# BSD LICENSE
#
# Copyright(c) <2019> Intel Corporation. All rights reserved.
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
# 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
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

"""

import re
import time

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.qemu_kvm import QEMUKvm
from framework.test_case import TestCase

RSS_KEY = "6EA6A420D5138E712433B813AE45B3C4BECB2B405F31AD6C331835372D15E2D5E49566EE0ED1962AFA1B7932F3549520FD71C75E"
PACKET_COUNT = 100


class TestRuntimeVfQn(TestCase):
    supported_vf_driver = ["pci-stub", "vfio-pci"]

    def set_up_all(self):
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.src_intf = self.tester.get_interface(self.tester.get_local_port(0))
        self.src_mac = self.tester.get_mac(self.tester.get_local_port(0))
        self.dst_mac = self.dut.get_mac_address(0)
        self.vm0 = None
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]["pci"]
        self.used_dut_port = self.dut_ports[0]
        self.vf_mac = "00:11:22:33:44:55"
        self.pmdout = PmdOutput(self.dut)

    def set_up(self):
        self.dut.kill_all()
        self.host_testpmd = PmdOutput(self.dut)
        self.setup_vm_env(driver="igb_uio")

    def setup_vm_env(self, driver="default"):
        """
        setup qemu virtual environment,this is to set up 1pf and 2vfs environment, the pf can be bond to
        kernel driver or dpdk driver.
        """
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 2, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port]["vfs_port"]

        # set vf assign method and vf driver
        self.vf_driver = self.get_suite_cfg()["vf_driver"]
        if self.vf_driver is None:
            self.vf_driver = "pci-stub"
        self.verify(self.vf_driver in self.supported_vf_driver, "Unspported vf driver")
        if self.vf_driver == "pci-stub":
            self.vf_assign_method = "pci-assign"
        else:
            self.vf_assign_method = "vfio-pci"
            self.dut.send_expect("modprobe vfio-pci", "#")

        try:
            for port in self.sriov_vfs_port_0:
                port.bind_driver(self.vf_driver)

            time.sleep(1)
            vf0_prop = {"opt_host": self.sriov_vfs_port_0[0].pci}
            vf1_prop = {"opt_host": self.sriov_vfs_port_0[1].pci}

            # set up VM0 ENV
            self.vm0 = QEMUKvm(self.dut, "vm0", "vf_queue_number")
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop)
            self.vm_dut_0 = self.vm0.start()
            if self.vm_dut_0 is None:
                raise Exception("Set up VM0 ENV failed!")
        except Exception as e:
            self.logger.info(e)
            self.destroy_vm_env()
            raise Exception(e)

    def destroy_vm_env(self):
        # destroy vm0
        if getattr(self, "vm0", None) and self.vm0:
            self.vm0_dut_ports = None
            self.vm0.stop()
            self.vm0 = None

        # destroy host testpmd
        if getattr(self, "host_testpmd", None):
            self.host_testpmd.execute_cmd("quit", "# ")
            self.host_testpmd = None

        # reset used port's sriov
        if getattr(self, "used_dut_port", None):
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            port = self.dut.ports_info[self.used_dut_port]["port"]
            port.bind_driver()
            self.used_dut_port = None

        # bind used ports with default driver
        for port_id in self.dut_ports:
            port = self.dut.ports_info[port_id]["port"]
            port.bind_driver()

    def send_packet(self, vf_mac, itf, integer):
        """
        Sends packets.
        """
        pkt = Packet()
        pkt.generate_random_pkts(vf_mac, pktnum=integer, random_type=["IP_RAW"])
        pkt.send_pkt(self.tester, tx_port=itf)

    def verify_queue_number(self, outstring, qn, pkt_count):
        total_rx = []
        total_tx = []
        total_rx_pkt = []
        total_tx_pkt = []
        lines = outstring.split("\r\n")
        re_rx_q = r"RX Port= 0/Queue=\s?([0-9]+)"
        re_tx_q = r"TX Port= 0/Queue=\s?([0-9]+)"
        re_rx_pkt = r"RX-packets:\s?([0-9]+)"
        re_tx_pkt = r"TX-packets:\s?([0-9]+)"
        rx_s = re.compile(re_rx_q, re.DOTALL)
        tx_s = re.compile(re_tx_q, re.DOTALL)
        rx_pkt_s = re.compile(re_rx_pkt, re.DOTALL)
        tx_pkt_s = re.compile(re_tx_pkt, re.DOTALL)
        for line in lines:
            line = line.strip()
            if line.strip().startswith("------- Forward"):
                rx_pkt = rx_s.search(line)
                tx_pkt = tx_s.search(line)
                total_rx.append(int(rx_pkt.group(1)))
                total_tx.append(int(tx_pkt.group(1)))
            elif "RX-packets" in line and "TX-packets" in line and "TX-dropped" in line:
                self.logger.info(line)
                q_rx_pkt = rx_pkt_s.search(line)
                q_tx_pkt = tx_pkt_s.search(line)
                total_rx_pkt.append(int(q_rx_pkt.group(1)))
                total_tx_pkt.append(int(q_tx_pkt.group(1)))
            else:
                continue
        self.verify(
            len(total_rx) == len(total_tx) == qn,
            "RX queue number is not equal to Tx queue number.",
        )
        self.verify(
            sum(total_rx_pkt) == sum(total_tx_pkt) == pkt_count, "some packets lost."
        )

    def stop_vm0(self):
        if getattr(self, "vm0", None) and self.vm0:
            self.vm0_dut_ports = None
            self.vm0.stop()
            self.vm0 = None

    def execute_testpmd_cmd(self, cmds):
        if len(cmds) == 0:
            return
        for item in cmds:
            if len(item) == 2:
                self.vm0_testpmd.execute_cmd(item[0], int(item[1]))
            else:
                self.vm0_testpmd.execute_cmd(item[0])

    def testpmd_config_cmd_list(self, qn):
        cmd_list = [
            ["stop"],
            ["port stop all"],
            ["port config all txq %d" % qn],
            ["port config all rxq %d" % qn],
            ["port start all"],
            ["port config 0 rss-hash-key ipv4 %s" % RSS_KEY],
        ]
        return cmd_list

    def verify_result(self, queue_num, pkt_num):
        if queue_num == 1:
            outstring = self.vm0_testpmd.execute_cmd("start", "testpmd> ")
            self.verify(
                "port 0: RX queue number: 1 Tx queue number: 1" in outstring,
                "The RX/TX queue number error.",
            )
            self.vm0_dut_ports = self.vm_dut_0.get_ports("any")
            self.vf_mac = self.vm0_testpmd.get_port_mac(self.vm0_dut_ports[0])
            self.send_packet(self.vf_mac, self.src_intf, 3)
            out = self.vm0_testpmd.get_output()
            self.verify(
                "port 0/queue 0: received 1 packets" in out,
                "queue 0 can not receive pkt",
            )
        else:
            outstring = self.vm0_testpmd.execute_cmd("start", "testpmd> ", 120)
            self.logger.info(outstring)
            time.sleep(2)
            self.verify(
                "port 0: RX queue number: %d Tx queue number: %d"
                % (queue_num, queue_num)
                in outstring,
                "The RX/TX queue number error.",
            )
            self.vm0_dut_ports = self.vm_dut_0.get_ports("any")
            self.vf_mac = self.vm0_testpmd.get_port_mac(self.vm0_dut_ports[0])
            self.send_packet(self.vf_mac, self.src_intf, pkt_num)
            outstring1 = self.vm0_testpmd.execute_cmd("stop", "testpmd> ", 120)
            time.sleep(2)
            self.verify_queue_number(outstring1, queue_num, pkt_num)

    def test_reserve_valid_vf_qn(self):
        """
        Test case 1: reserve valid vf queue number
        :return:
        """
        valid_qn = (
            2,
            4,
            8,
        )
        for qn in valid_qn:
            host_eal_param = (
                "-a %s,queue-num-per-vf=%d --file-prefix=test1 --socket-mem 1024,1024"
                % (self.pf_pci, qn)
            )
            self.host_testpmd.start_testpmd(
                self.pmdout.default_cores, param="", eal_param=host_eal_param
            )

            gest_eal_param = (
                "-a %s --file-prefix=test2" % self.vm_dut_0.ports_info[0]["pci"]
            )
            self.vm0_testpmd = PmdOutput(self.vm_dut_0)
            self.vm0_testpmd.start_testpmd(
                self.pmdout.default_cores, eal_param=gest_eal_param, param=""
            )
            guest_cmds = self.testpmd_config_cmd_list(qn)
            self.execute_testpmd_cmd(guest_cmds)
            outstring = self.vm0_testpmd.execute_cmd("start", "testpmd> ")
            self.logger.info(outstring)
            self.verify(
                "port 0: RX queue number: %d Tx queue number: %d" % (qn, qn)
                in outstring,
                "The RX/TX queue number error.",
            )
            self.vm0_dut_ports = self.vm_dut_0.get_ports("any")
            self.vf_mac = self.vm0_testpmd.get_port_mac(self.vm0_dut_ports[0])
            self.send_packet(self.vf_mac, self.src_intf, PACKET_COUNT)
            outstring1 = self.vm0_testpmd.execute_cmd("stop", "testpmd> ")
            self.verify_queue_number(outstring1, qn, PACKET_COUNT)
            guest_cmds1 = self.testpmd_config_cmd_list(qn + 1)
            self.execute_testpmd_cmd(guest_cmds1)
            outstring2 = self.vm0_testpmd.execute_cmd("start", "testpmd> ")
            self.logger.info(outstring2)
            self.verify(
                "port 0: RX queue number: %d Tx queue number: %d" % ((qn + 1), (qn + 1))
                in outstring2,
                "The RX/TX queue number error.",
            )
            self.send_packet(self.vf_mac, self.src_intf, PACKET_COUNT)
            outstring3 = self.vm0_testpmd.execute_cmd("stop", "testpmd> ")
            self.logger.info(outstring3)
            self.verify_queue_number(outstring3, qn + 1, PACKET_COUNT)
            self.vm0_testpmd.execute_cmd("quit", "# ")
            self.dut.send_expect("quit", "# ")

    def test_reserve_invalid_vf_qn(self):
        """
        Test case 2: reserve invalid VF queue number
        :return:
        """
        for invalid_qn in (
            0,
            3,
            5,
            6,
            7,
            9,
            11,
            15,
            17,
            25,
        ):
            eal_param = (
                "-a %s,queue-num-per-vf=%d --file-prefix=test1 --socket-mem 1024,1024"
                % (self.pf_pci, invalid_qn)
            )
            testpmd_out = self.host_testpmd.start_testpmd(
                self.pmdout.default_cores, param="", eal_param=eal_param
            )
            self.verify(
                "it must be power of 2 and equal or less than 16" in testpmd_out,
                "there is no 'Wrong VF queue number = 0' logs.",
            )
            self.dut.send_expect("quit", "# ")

    def test_set_valid_vf_qn_in_testpmd(self):
        """
        Test case 3: set valid VF queue number in testpmd command-line options
        :return:
        """
        host_eal_param = (
            "-a %s --file-prefix=test1 --socket-mem 1024,1024" % self.pf_pci
        )
        self.host_testpmd.start_testpmd(
            self.pmdout.default_cores, param="", eal_param=host_eal_param
        )

        gest_eal_param = (
            "-a %s --file-prefix=test2" % self.vm_dut_0.ports_info[0]["pci"]
        )
        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        for valid_qn in range(1, 17):
            count = valid_qn * 10
            if valid_qn == 1:
                self.vm0_testpmd.start_testpmd(
                    self.pmdout.default_cores,
                    eal_param=gest_eal_param,
                    param=" --rxq=1 --txq=1",
                )
                self.vm0_testpmd.execute_cmd("set verbose 1")
                self.vm0_testpmd.execute_cmd("set promisc all off", "testpmd> ")
                self.vm0_testpmd.execute_cmd("set fwd mac", "testpmd> ")
                self.vm0_testpmd.execute_cmd(
                    "port config 0 rss-hash-key ipv4 %s" % RSS_KEY
                )
                self.verify_result(valid_qn, count)
                self.vm0_testpmd.execute_cmd("quit", "# ")
            else:
                self.vm0_testpmd.start_testpmd(
                    self.pmdout.default_cores,
                    eal_param=gest_eal_param,
                    param=" --rxq=%d --txq=%d" % (valid_qn, valid_qn),
                )
                self.vm0_testpmd.execute_cmd("set promisc all off", "testpmd> ")
                self.vm0_testpmd.execute_cmd("set fwd mac", "testpmd> ")
                self.vm0_testpmd.execute_cmd(
                    "port config 0 rss-hash-key ipv4 %s" % RSS_KEY
                )
                self.verify_result(valid_qn, count)
                self.vm0_testpmd.execute_cmd("quit", "# ")

    def test_set_invalid_vf_qn_in_testpmd(self):
        """
        Test case 4: set invalid VF queue number in testpmd command-line options
        :return:
        """
        host_eal_param = (
            "-a %s --file-prefix=test1 --socket-mem 1024,1024" % self.pf_pci
        )
        self.host_testpmd.start_testpmd(
            self.pmdout.default_cores, param="", eal_param=host_eal_param
        )
        gest_eal_param = (
            "-a %s --file-prefix=test2" % self.vm_dut_0.ports_info[0]["pci"]
        )
        self.vm0_testpmd = PmdOutput(self.vm_dut_0)

        app_name = self.dut.apps_name["test-pmd"]
        command_0 = app_name + "-c %s -n %d %s -- -i %s" % (
            "0xf",
            self.dut.get_memory_channels(),
            gest_eal_param,
            " --rxq=0 --txq=0",
        )
        outstring = self.vm0_testpmd.execute_cmd(command_0, expected="# ")
        self.verify(
            "Either rx or tx queues should be non-zero" in outstring,
            "The output of testpmd start is different from expect when set invalid VF queue number 0.",
        )
        time.sleep(2)
        command_257 = app_name + "-c %s -n %d %s -- -i %s" % (
            "0xf",
            self.dut.get_memory_channels(),
            gest_eal_param,
            " --rxq=257 --txq=257",
        )
        outstring1 = self.vm0_testpmd.execute_cmd(command_257, expected="# ")
        self.verify(
            "rxq 257 invalid - must be >= 0 && <= 256" in outstring1,
            "The output of testpmd start is different from expect when set invalid VF queue number 257.",
        )

    def test_set_valid_vf_qn_with_testpmd_func_cmd(self):
        """
        Test case 5: set valid VF queue number with testpmd function command
        :return:
        """
        host_eal_param = (
            "-a %s --file-prefix=test1 --socket-mem 1024,1024" % self.pf_pci
        )
        self.host_testpmd.start_testpmd(
            self.pmdout.default_cores, param="", eal_param=host_eal_param
        )

        gest_eal_param = (
            "-a %s --file-prefix=test2" % self.vm_dut_0.ports_info[0]["pci"]
        )
        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.vm0_testpmd.start_testpmd(
            self.pmdout.default_cores, eal_param=gest_eal_param, param=""
        )
        for valid_qn in range(1, 17):
            count = valid_qn * 10
            if valid_qn == 1:
                guest_cmds = self.testpmd_config_cmd_list(1)
                guest_cmds.insert(0, ["set fwd mac"])
                guest_cmds.insert(0, ["set promisc all off"])
                guest_cmds.insert(0, ["set verbose 1"])
                self.execute_testpmd_cmd(guest_cmds)
                self.verify_result(valid_qn, count)
            else:
                guest_cmds = self.testpmd_config_cmd_list(valid_qn)
                guest_cmds.insert(0, ["set fwd mac"])
                guest_cmds.insert(0, ["set promisc all off"])
                self.execute_testpmd_cmd(guest_cmds)
                self.verify_result(valid_qn, count)
        self.vm0_testpmd.execute_cmd("quit", "# ")

    def test_set_invalid_vf_qn_with_testpmd_func_cmd(self):
        """
        Test case 6: set invalid VF queue number with testpmd function command
        :return:
        """
        expect_str = [
            "Warning: Either rx or tx queues should be non zero",
            "Fail: input rxq (257) can't be greater than max_rx_queues (256) of port 0",
            "Fail: input txq (257) can't be greater than max_tx_queues (256) of port 0",
        ]
        host_eal_param = (
            "-a %s --file-prefix=test1 --socket-mem 1024,1024" % self.pf_pci
        )
        self.host_testpmd.start_testpmd(
            self.pmdout.default_cores, param="", eal_param=host_eal_param
        )
        gest_eal_param = (
            "-a %s --file-prefix=test2" % self.vm_dut_0.ports_info[0]["pci"]
        )
        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.vm0_testpmd.start_testpmd(
            self.pmdout.default_cores, eal_param=gest_eal_param, param=""
        )
        for invalid_qn in [0, 257]:
            self.vm0_testpmd.execute_cmd("port stop all")
            rxq_output = self.vm0_testpmd.execute_cmd(
                "port config all rxq %d" % invalid_qn
            )
            txq_output = self.vm0_testpmd.execute_cmd(
                "port config all txq %d" % invalid_qn
            )
            self.verify(
                rxq_output or txq_output in expect_str, "The output is not expect."
            )
            self.vm0_testpmd.execute_cmd("port start all")
        self.vm0_testpmd.execute_cmd("quit", "# ")

    def test_reserve_vf_qn(self):
        """
        Test case 7: Reserve VF queue number when VF bind to kernel driver
        :return:
        """
        host_eal_param = (
            "-a %s,queue-num-per-vf=2 --file-prefix=test1 --socket-mem 1024,1024"
            % self.pf_pci
        )
        self.host_testpmd.start_testpmd(
            self.pmdout.default_cores, param="", eal_param=host_eal_param
        )
        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.vm_dut_0.restore_interfaces()
        # wait few seconds for link ready
        countdown = 60
        while countdown:
            nic_info = self.vm0_testpmd.execute_cmd(
                "./usertools/dpdk-devbind.py -s | grep %s"
                % self.vm_dut_0.ports_info[0]["pci"],
                expected="# ",
            )
            inf_str = nic_info.split("if=")[1]
            inf = inf_str.split(" ")[0]
            if "drv" not in inf and inf != "":
                break
            else:
                time.sleep(0.01)
                countdown -= 1
                continue
        output = self.vm0_testpmd.execute_cmd("ethtool -S %s" % inf, expected="# ")
        self.verify(
            "tx-0.packets" in output and "tx-1.packets" in output,
            "VF0 rxq and txq number is not 2.",
        )

    def tear_down(self):
        self.stop_vm0()
        self.dut.send_expect("quit", "# ")

    def tear_down_all(self):
        self.destroy_vm_env()
        for port_id in self.dut_ports:
            self.dut.destroy_sriov_vfs_by_port(port_id)
