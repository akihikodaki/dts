# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019-2020 Intel Corporation
#

"""
DPDK Test suite.
Test QOS API in DPDK.
The DUT must have two 10G Ethernet ports connected to two ports of IXIA.
"""
import os

from framework.packet import Packet
from framework.pktgen import TRANSMIT_CONT
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase


class TestQosMeter(TestCase):
    def set_up_all(self):
        """
        ip_fragmentation Prerequisites
        """
        # Based on h/w type, choose how many ports to use
        ports = self.dut.get_ports()
        self.dut_ports = self.dut.get_ports(self.nic)
        self.tx_port = self.tester.get_local_port(self.dut_ports[0])
        self.rx_port = self.tester.get_local_port(self.dut_ports[1])
        self.pmdout = PmdOutput(self.dut)

        # Verify that enough ports are available
        self.verify(len(ports) >= 2, "Insufficient ports for testing")

        # get data from https://doc.dpdk.org/guides/sample_app_ug/qos_metering.html
        self.blind_pps = 14880000
        self.aware_pps = 13880000

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def build_app_and_send_package(self, payload_size_block):
        """
        Build app and send pkt
        return bps and pps
        """
        self.dut.send_expect(
            "rm -rf ./examples/qos_meter/build",
            "#",
        )
        out = self.dut.build_dpdk_apps("./examples/qos_meter")
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")
        eal_params = self.dut.create_eal_parameters(
            cores="1S/1C/1T", fixed_prefix=True, prefix="qos_meter"
        )
        app_name = self.dut.apps_name["qos_meter"]
        cmd = app_name + eal_params + "-- -p 0x3"
        self.dut.send_expect(cmd, "TX = 1")
        payload_size = payload_size_block - HEADER_SIZE["eth"] - HEADER_SIZE["ip"]
        dts_mac = self.dut.get_mac_address(self.dut_ports[self.rx_port])
        pkt = Packet(pkt_type="IP_RAW", pkt_len=payload_size)
        pkt.save_pcapfile(self.tester, "%s/tester.pcap" % self.tester.tmp_file)
        stream_option = {
            "pcap": "%s/tester.pcap" % self.tester.tmp_file,
            "stream_config": {
                "rate": 100,
                "transmit_mode": TRANSMIT_CONT,
            },
        }
        self.tester.pktgen.clear_streams()
        stream_ids = []
        stream_id = self.tester.pktgen.add_stream(
            self.tx_port, self.rx_port, "%s/tester.pcap" % self.tester.tmp_file
        )
        self.tester.pktgen.config_stream(stream_id, stream_option)
        stream_ids.append(stream_id)
        stream_id = self.tester.pktgen.add_stream(
            self.rx_port, self.tx_port, "%s/tester.pcap" % self.tester.tmp_file
        )
        self.tester.pktgen.config_stream(stream_id, stream_option)
        stream_ids.append(stream_id)
        traffic_opt = {"method": "throughput", "rate": 100, "duration": 20}
        bps, pps = self.tester.pktgen.measure(stream_ids, traffic_opt)
        return bps, pps

    def verify_throughput(self, throughput, pps):
        difference_value = throughput - pps
        # performance data is allowed to float by 10%
        self.verify(
            -pps * 0.1 < difference_value < pps * 0.1, "throughput validation failure"
        )

    def test_perf_srTCM_blind_RED(self):
        """
        srTCM blind RED
        """
        self.dut.send_expect(
            r"sed -i -e '/#define APP_PKT_COLOR_POS/s/[0-9]/5/g' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '/^#define APP_MODE /s/APP_MODE_*/APP_MODE_SRTCM_COLOR_BLIND/2' ./examples/qos_meter/main.c",
            "#",
        )
        bps, pps = self.build_app_and_send_package(64)
        self.verify_throughput(pps, self.aware_pps)

    def test_perf_srTCM_blind_GREEN(self):
        """
        srTCM blind GREEN
        """
        self.dut.send_expect(
            r"sed -i -e '/#define APP_PKT_COLOR_POS/s/[0-9]/3/g' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '/^#define APP_MODE /s/APP_MODE_*/APP_MODE_SRTCM_COLOR_BLIND/2' ./examples/qos_meter/main.c",
            "#",
        )
        bps, pps = self.build_app_and_send_package(64)
        self.verify_throughput(pps, self.blind_pps)

    def test_perf_srTCM_aware_RED(self):
        """
        srTCM aware RED
        """
        self.dut.send_expect(
            r"sed -i -e '/#define APP_PKT_COLOR_POS/s/[0-9]/5/g' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '/^#define APP_MODE /s/APP_MODE_*/APP_MODE_SRTCM_COLOR_AWARE/2' ./examples/qos_meter/main.c",
            "#",
        )
        bps, pps = self.build_app_and_send_package(64)
        self.verify_throughput(pps, self.blind_pps)

    def test_perf_trTCM_blind(self):
        """
        trTCM blind
        """
        self.dut.send_expect(
            r"sed -i -e '/#define APP_PKT_COLOR_POS/s/[0-9]/5/g' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '/^#define APP_MODE /s/APP_MODE_*/APP_MODE_TRTCM_COLOR_BLIND/2' ./examples/qos_meter/main.c",
            "#",
        )
        bps, pps = self.build_app_and_send_package(64)
        self.verify_throughput(pps, self.aware_pps)

    def test_perf_trTCM_aware(self):
        """
        trTCM aware
        """
        self.dut.send_expect(
            r"sed -i -e '/#define APP_PKT_COLOR_POS/s/[0-9]/5/g' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '/^#define APP_MODE /s/APP_MODE_*/APP_MODE_TRTCM_COLOR_AWARE/2' ./examples/qos_meter/main.c",
            "#",
        )
        bps, pps = self.build_app_and_send_package(64)
        self.verify_throughput(pps, self.blind_pps)

    def test_perf_trTCM_blind_changed_CBS_EBS_64B_frame(self):
        """
        trTCM blind changed CBS and EBS
        """
        self.dut.send_expect(
            r"sed -i -e '/#define APP_PKT_COLOR_POS/s/[0-9]/5/g' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '/^#define APP_MODE\s/s/APP_MODE_.*/APP_MODE_TRTCM_COLOR_BLIND/' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '91 s/cbs = [0-9]*,/cbs = 64,/' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '100 s/cbs = [0-9]*,/cbs = 64,/' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '92 s/[0-9]*$/512/' ./examples/qos_meter/main.c",
            "#",
        )
        bps, pps = self.build_app_and_send_package(64)
        self.verify_throughput(pps, self.blind_pps)

    def test_perf_trTCM_blind_changed_CBS_EBS_82B_frame(self):
        """
        trTCM blind changed CBS and EBS
        """
        self.dut.send_expect(
            r"sed -i -e '/#define APP_PKT_COLOR_POS/s/[0-9]/5/g' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '/^#define APP_MODE\s/s/APP_MODE_.*/APP_MODE_SRTCM_COLOR_BLIND/' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '91 s/cbs = [0-9]*,/cbs = 64,/' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '100 s/cbs = [0-9]*,/cbs = 64,/' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '92 s/[0-9]*$/512/' ./examples/qos_meter/main.c",
            "#",
        )
        bps, pps = self.build_app_and_send_package(82)
        self.verify_throughput(pps, self.blind_pps)

    def test_perf_trTCM_blind_changed_CBS_EBS_83B_frame(self):
        """
        trTCM blind changed CBS and EBS
        """
        self.dut.send_expect(
            r"sed -i -e '/#define APP_PKT_COLOR_POS/s/[0-9]/5/g' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '/^#define APP_MODE\s/s/APP_MODE_.*/APP_MODE_SRTCM_COLOR_BLIND/' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '91 s/cbs = [0-9]*,/cbs = 64,/' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '100 s/cbs = [0-9]*,/cbs = 64,/' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '92 s/[0-9]*$/512/' ./examples/qos_meter/main.c",
            "#",
        )
        bps, pps = self.build_app_and_send_package(83)
        self.verify_throughput(pps, self.blind_pps)

    def test_perf_trTCM_blind_changed_CBS_EBS_146B_frame(self):
        """
        trTCM blind changed CBS and EBS
        """
        tc_pps = 10000000
        self.dut.send_expect(
            r"sed -i -e '/#define APP_PKT_COLOR_POS/s/[0-9]/5/g' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '/^#define APP_MODE\s/s/APP_MODE_.*/APP_MODE_SRTCM_COLOR_BLIND/' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '91 s/cbs = [0-9]*,/cbs = 64,/' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '100 s/cbs = [0-9]*,/cbs = 64,/' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '92 s/[0-9]*$/512/' ./examples/qos_meter/main.c",
            "#",
        )
        bps, pps = self.build_app_and_send_package(146)
        self.verify_throughput(pps, tc_pps)

    def test_perf_trTCM_blind_changed_CBS_EBS_530B_frame(self):
        """
        trTCM blind changed CBS and EBS
        """
        tc_pps = 2500000
        self.dut.send_expect(
            r"sed -i -e '/#define APP_PKT_COLOR_POS/s/[0-9]/5/g' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '/^#define APP_MODE\s/s/APP_MODE_.*/APP_MODE_SRTCM_COLOR_BLIND/' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '91 s/cbs = [0-9]*,/cbs = 64,/' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '100 s/cbs = [0-9]*,/cbs = 64,/' ./examples/qos_meter/main.c",
            "#",
        )
        self.dut.send_expect(
            r"sed -i -e '92 s/[0-9]*$/512/' ./examples/qos_meter/main.c",
            "#",
        )
        bps, pps = self.build_app_and_send_package(530)
        self.verify_throughput(pps, tc_pps)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
