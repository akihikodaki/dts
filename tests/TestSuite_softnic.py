# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

"""
DPDK Test suite.
Test softnic API in DPDK.
"""

import itertools
import os
import re
import string
import time
import traceback
from time import sleep

import scapy.layers.inet
from scapy.arch import get_if_hwaddr
from scapy.packet import Raw, bind_layers
from scapy.route import *
from scapy.sendrecv import sendp, sniff
from scapy.utils import hexstr, rdpcap, wrpcap

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestSoftnic(TestCase):
    def pair_hex_digits(self, iterable, count, fillvalue=None):
        args = [iter(iterable)] * count
        return itertools.zip_longest(*args, fillvalue=fillvalue)

    def get_flow_direction_param_of_tcpdump(self):
        """
        get flow dirction param depend on tcpdump version
        """
        param = ""
        direct_param = r"(\s+)\[ (\S+) in\|out\|inout \]"
        out = self.tester.send_expect("tcpdump -h", "# ", trim_whitespace=False)
        for line in out.split("\n"):
            m = re.match(direct_param, line)
            if m:
                opt = re.search("-Q", m.group(2))
                if opt:
                    param = "-Q" + " in"
                else:
                    opt = re.search("-P", m.group(2))
                    if opt:
                        param = "-P" + " in"
        if len(param) == 0:
            self.logger.info("tcpdump not support direction choice!!!")
        return param

    def tcpdump_start_sniff(self, interface, filters=""):
        """
        Starts tcpdump in the background to sniff packets that received by interface.
        """
        cmd = "rm -f /tmp/tcpdump_{0}.pcap".format(interface)
        self.tester.send_expect(cmd, "#")
        cmd = "tcpdump -nn -e {0} -w /tmp/tcpdump_{1}.pcap -i {1} {2} -Q in 2>/tmp/tcpdump_{1}.out &".format(
            self.param_flow_dir, interface, filters
        )
        self.tester.send_expect(cmd, "# ")

    def tcpdump_stop_sniff(self):
        """
        Stops the tcpdump process running in the background.
        """
        self.tester.send_expect("killall tcpdump", "# ")
        # For the [pid]+ Done tcpdump... message after killing the process
        sleep(1)
        self.tester.send_expect('echo "Cleaning buffer"', "# ")
        sleep(1)

    def compare_packets(self, in_file, out_file, all_pkts):
        """
        Flag all_pkt is zero, then it compares small packet(size upto 48 bytes).
        Flag all_pkt is non-zero, then it compares all packets of out_file.
        """
        if all_pkts == 0:
            cmd = "diff -sqw <(head -n 11 {}) <(head -n 11 {})".format(
                in_file, out_file
            )
        else:
            cmd = "diff -sqw {} {}".format(in_file, out_file)
        return self.tester.send_command(cmd, timeout=0.5)

    def convert_tcpdump_to_text2pcap(self, in_filename, out_filename):
        with open(in_filename) as input, open(out_filename, "w") as output:
            output.write("# SPDX-License-Identifier: BSD-3-Clause\n")
            output.write("# Copyright(c) 2022 Intel Corporation\n")
            output.write("#\n\n")
            output.write("# text to pcap: text2pcap packet.txt packet.pcap\n")
            output.write("# pcap to text: tcpdump -r packet.pcap -xx\n\n")

            i = 0
            for line in input:
                time = self.pkt_timestamp.match(line)
                if time:
                    output.write("# Packet {}\n".format(i))
                    i += 1
                    continue
                payload = self.pkt_content.match(line)
                if payload:
                    address = payload.group(1)
                    hex_data = payload.group(2).replace(" ", "")
                    hex_data = " ".join(
                        "".join(part) for part in self.pair_hex_digits(hex_data, 2, " ")
                    )
                    output.write("{:0>6}  {:<47}\n".format(address, hex_data))

    def send_and_sniff(
        self, from_port, to_port, in_pcap, out_pcap, filters, all_pkts=0
    ):
        self.tester.send_expect("rm -f /tmp/*.txt /tmp/*.pcap /tmp/*.out", "# ")
        tx_count = len(from_port)
        rx_count = len(to_port)
        tx_port, rx_port, tx_inf, rx_inf = ([] for i in range(4))

        for i in range(tx_count):
            tx_port.append(self.tester.get_local_port(self.dut_ports[from_port[i]]))
            tx_inf.append(self.tester.get_interface(tx_port[i]).strip())

        for i in range(rx_count):
            rx_port.append(self.tester.get_local_port(self.dut_ports[to_port[i]]))
            rx_inf.append(self.tester.get_interface(rx_port[i]).strip())
            self.tcpdump_start_sniff(rx_inf[i], filters[i])

        self.tester.scapy_foreground()
        for i in range(tx_count):
            self.tester.send_expect(
                "text2pcap -q {} /tmp/tx_{}.pcap".format(
                    self.src_path + in_pcap[i], tx_inf[i]
                ),
                "# ",
            )
            self.tester.scapy_append(
                'pkt = rdpcap("/tmp/tx_{}.pcap")'.format(tx_inf[i])
            )

            self.tester.scapy_append(
                'sendp(pkt, iface="{}", count=32)'.format(tx_inf[i])
            )

        self.tester.scapy_execute()
        self.tcpdump_stop_sniff()
        mismatch_count = 0

        for i in range(rx_count):
            self.tester.send_expect(
                "tcpdump -n -r /tmp/tcpdump_{}.pcap -xx > /tmp/packet_rx.txt".format(
                    rx_inf[i]
                ),
                "# ",
            )
            self.convert_tcpdump_to_text2pcap(
                "/tmp/packet_rx.txt", "/tmp/packet_rx_rcv_{}.txt".format(rx_inf[i])
            )
            out = self.compare_packets(
                "/tmp/packet_rx_rcv_{}.txt".format(rx_inf[i]),
                self.src_path + out_pcap[i],
                all_pkts,
            )
            if "are identical" not in out:
                return False
        return True

    def set_up_all(self):
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports()

        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.def_driver = self.dut.ports_info[self.dut_ports[0]][
            "port"
        ].get_nic_driver()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        # Verify that enough threads are available
        cores = self.dut.get_core_list("1S/1C/1T")
        self.verify(cores is not None, "Insufficient cores for speed testing")
        self.param_flow_dir = self.get_flow_direction_param_of_tcpdump()

        # setting up source and destination location
        self.dst_path = "/tmp/"
        FILE_DIR = os.path.dirname(os.path.abspath(__file__)).split(os.path.sep)
        self.src_path = os.path.sep.join(FILE_DIR[:-1]) + "/dep/"
        SOFTNIC_TAR_FOLDER = self.src_path + "softnic"

        # copy dependancies to the DUT
        self.tester.send_expect("rm -rf /tmp/softnic.tar.gz", "# ")
        self.tester.send_expect(
            "tar -zcf /tmp/softnic.tar.gz --absolute-names {}".format(self.src_path),
            "# ",
            20,
        )
        self.dut.send_expect("rm -rf /tmp/softnic.tar.gz /tmp/softnic", "# ", 20)
        self.dut.session.copy_file_to("/tmp/softnic.tar.gz", self.dst_path)
        self.dut.send_expect(
            "tar -zxf /tmp/softnic.tar.gz --strip-components={} --absolute-names --directory /tmp".format(
                SOFTNIC_TAR_FOLDER.count("/") - 1
            ),
            "# ",
            20,
        )

        self.eal_param = " ".join(
            " -a " + port_info["pci"] for port_info in self.dut.ports_info
        )
        self.path = self.dut.apps_name["test-pmd"]
        self.pmdout = PmdOutput(self.dut)

        # create packet matching regular expression
        self.pkt_timestamp = re.compile(r"\d{2}\:\d{2}\:\d{2}\.\d{6}")
        self.pkt_content = re.compile(r"\t0x([0-9a-fA-F]+):  ([0-9a-fA-F ]+)")

        # get dts output path
        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        else:
            cur_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            self.output_path = os.sep.join([cur_path, self.logger.log_path])
        # bind the ports
        self.dut.bind_interfaces_linux(self.drivername, [self.dut_ports[0]])

    def set_up(self):
        """
        Run before each test case.
        """

    def run_test_pmd(self, file_name):
        try:
            cmd = 'test -f {} && echo "File exists!"'.format(file_name)
            self.dut.send_expect(cmd, "File exists!", 1)

            self.pmdout.start_testpmd(
                list(range(3)),
                "--portmask=0x2",
                eal_param="-s 0x4 %s --vdev 'net_softnic0,firmware=%s,cpu_id=1,conn_port=8086'"
                % (self.eal_param, file_name),
            )
        except Exception:
            trace = traceback.format_exc()
            self.logger.error("Error while running testpmd:\n" + trace)

    def test_rx_tx(self):
        cli_file = "/tmp/softnic/rx_tx/rx_tx.cli"
        self.run_test_pmd(cli_file)
        sleep(5)
        self.dut.send_expect("start", "testpmd>")

        in_pcap = ["softnic/rx_tx/pcap_files/in.txt"]
        out_pcap = ["softnic/rx_tx/pcap_files/out.txt"]
        filters = ["tcp"]
        tx_port = [0]
        rx_port = [0]
        result = self.send_and_sniff(tx_port, rx_port, in_pcap, out_pcap, filters)
        if result:
            self.dut.send_expect("stop", "testpmd>")
        else:
            self.verify(False, "Output pcap files mismatch error")

        """
        Add new test cases here.
        """

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("quit", "# ")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
