# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
"""
from time import sleep

from scapy.layers.inet import IP, Ether
from scapy.utils import wrpcap

import framework.utils as utils
from framework.test_case import TestCase


#
#
# Test class.
#
class TestPmdPcap(TestCase):

    pcap_file_sizes = [1000, 500]
    dut_pcap_files_path = "/root/"

    def set_up_all(self):
        self.check_scapy_in_dut()

        self.memory_channel = self.dut.get_memory_channels()

        # make sure there is no interface to bind
        # because if there is any interface bonded to igb_uio,
        # it will result in packet transmitting failed
        self.dut.restore_interfaces()
        os_type = self.dut.get_os_type()
        if os_type == "freebsd":
            self.dut.send_expect(
                "kldload ./%s/kmod/contigmem.ko" % self.target, "#", 20
            )
        self.path = self.dut.apps_name["test-pmd"]

    def create_pcap_file(self, filename, number_of_packets):
        flow = []
        for pkt_id in range(number_of_packets):
            pkt_id = str(hex(pkt_id % 256))
            flow.append(
                Ether(src="00:00:00:00:00:%s" % pkt_id[2:], dst="00:00:00:00:00:00")
                / IP(src="192.168.1.1", dst="192.168.1.2")
                / ("X" * 26)
            )

        wrpcap(filename, flow)

    def check_scapy_in_dut(self):
        try:
            self.dut.send_expect("scapy", ">>> ")
            self.dut.send_expect("quit()", "# ")
        except:
            self.verify(False, "Scapy is required in dut.")

    def check_pcap_files(self, in_pcap, out_pcap, expected_frames):

        # Check if the number of expected frames are in the output
        result = self.dut.send_expect("tcpdump -n -e -r %s | wc -l" % out_pcap, "# ")
        self.verify(
            str(expected_frames) in result, "Not all packets have been forwarded"
        )

        # Check if the frames in the input and output files match
        self.dut.send_expect("scapy", ">>> ")
        self.dut.send_expect('input=rdpcap("%s")' % in_pcap, ">>> ")
        self.dut.send_expect('output=rdpcap("%s")' % out_pcap, ">>> ")
        self.dut.send_expect(
            "result=[input[i]==output[i] for i in range(len(input))]", ">>> "
        )
        result = self.dut.send_expect("False in result", ">>> ")
        self.dut.send_expect("quit()", "# ")

        self.verify("True" not in result, "In/Out packets do not match.")

    def test_send_packets_with_one_device(self):
        in_pcap = "in_pmdpcap.pcap"
        out_pcap = "/tmp/out_pmdpcap.pcap"

        two_cores = self.dut.get_core_list("1S/2C/1T")
        core_mask = utils.create_mask(two_cores)

        eal_para = self.dut.create_eal_parameters(cores="1S/2C/1T")
        self.create_pcap_file(in_pcap, TestPmdPcap.pcap_file_sizes[0])
        self.dut.session.copy_file_to(in_pcap)

        command = (
            "{} {} "
            + "--vdev=eth_pcap0,rx_pcap={},tx_pcap={} "
            + "-- -i --port-topology=chained --no-flush-rx"
        )

        self.dut.send_expect(
            command.format(
                self.path, eal_para, TestPmdPcap.dut_pcap_files_path + in_pcap, out_pcap
            ),
            "testpmd> ",
            15,
        )

        self.dut.send_expect("start", "testpmd> ")
        sleep(2)
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("quit", "# ")

        self.check_pcap_files(
            TestPmdPcap.dut_pcap_files_path + in_pcap,
            out_pcap,
            TestPmdPcap.pcap_file_sizes[0],
        )

    def test_send_packets_with_two_devices(self):

        in_pcap1 = "in1_pmdpcap.pcap"
        out_pcap1 = "/tmp/out1_pmdpcap.pcap"

        in_pcap2 = "in2_pmdpcap.pcap"
        out_pcap2 = "/tmp/out2_pmdpcap.pcap"

        four_cores = self.dut.get_core_list("1S/4C/1T")
        core_mask = utils.create_mask(four_cores)

        eal_para = self.dut.create_eal_parameters(cores="1S/4C/1T")
        self.create_pcap_file(in_pcap1, TestPmdPcap.pcap_file_sizes[0])
        self.dut.session.copy_file_to(in_pcap1)
        self.create_pcap_file(in_pcap2, TestPmdPcap.pcap_file_sizes[1])
        self.dut.session.copy_file_to(in_pcap2)

        command = (
            "{} {} "
            + "--vdev=eth_pcap0,rx_pcap={},tx_pcap={} "
            + "--vdev=eth_pcap1,rx_pcap={},tx_pcap={} "
            + "-- -i --no-flush-rx"
        )

        self.dut.send_expect(
            command.format(
                self.path,
                eal_para,
                TestPmdPcap.dut_pcap_files_path + in_pcap1,
                out_pcap1,
                TestPmdPcap.dut_pcap_files_path + in_pcap2,
                out_pcap2,
            ),
            "testpmd> ",
            15,
        )

        self.dut.send_expect("start", "testpmd> ")
        sleep(2)
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("quit", "# ")

        self.check_pcap_files(
            TestPmdPcap.dut_pcap_files_path + in_pcap1,
            out_pcap2,
            TestPmdPcap.pcap_file_sizes[0],
        )

        self.check_pcap_files(
            TestPmdPcap.dut_pcap_files_path + in_pcap2,
            out_pcap1,
            TestPmdPcap.pcap_file_sizes[1],
        )

    def tear_down_all(self):
        self.dut.set_target(self.target)
