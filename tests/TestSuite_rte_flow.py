# BSD LICENSE
#
# Copyright(c) 2020 Intel Corporation. All rights reserved.
# Copyright © 2018[, 2019] The University of New Hampshire. All rights reserved.
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
MTU Checks example.
"""
import time
import ipaddress
from typing import Callable

import utils
from pmd_output import PmdOutput
from test_case import TestCase

from test_case import TestCase

from framework.flow import generator


class RteFlow(TestCase):
    #
    #
    # Helper methods and setup methods.
    #
    # Some of these methods may not be used because they were inlined from a child
    # of TestCase. This was done because the current test system doesn't support
    # inheritance.
    #
    def exec(self, command: str) -> str:
        """
        An abstraction to remove repeated code throughout the subclasses of this class
        """
        return self.dut.send_expect(command, "testpmd>")

    def get_mac_address_for_port(self, port_id: int) -> str:
        return self.dut.get_mac_address(port_id)

    def send_scapy_packet(self, port_id: int, packet: str):
        itf = self.tester.get_interface(port_id)
        return self.tester.send_expect(f'sendp({packet}, iface="{itf}")', ">>>", timeout=30)

    def set_up_all(self):
        """
        Prerequisite steps for each test suit.
        """
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.rx_port = self.dut_ports[0]
        self.tx_port = self.dut_ports[1]

        self.pmdout = PmdOutput(self.dut)
        self.pmdout.start_testpmd("default", "--rxq 2 --txq 2")
        self.exec("set verbose 3")
        self.exec("set fwd rxonly")
        self.tester.send_expect("scapy", ">>>")

    def initialize_flow_rule(self, rule: str):
        output: str = self.exec(f"flow validate {self.dut_ports[0]} {rule}")
        if "Unsupported pattern" in output:
            return False

        output = self.exec(f"flow create {self.dut_ports[0]} {rule}")
        self.verify("created" in output or "Flow rule validated" in output, "Flow rule was not created: " + output)
        return True

    def send_packets(self, packets, pass_fail_function: Callable[[str], bool], error_message: str):
        for packet in packets:
            output = self.send_scapy_packet(0, packet)
            time.sleep(5)  # Allow the packet to be processed
            self.verify("Sent" in output, "Broken scapy packet definition: " + packet)
            output = self.pmdout.get_output()
            self.verify(pass_fail_function(output),
                        error_message + "\r\n" + output)

    def do_test_with_callable_tests_for_pass_fail(self, rule: str, pass_packets: frozenset, fail_packets: frozenset,
                                                  pass_check_function: Callable[[str], bool],
                                                  fail_check_function: Callable[[str], bool],
                                                  error_message: str):
        was_valid: bool = self.initialize_flow_rule(rule)
        if not was_valid:  # If a PMD rejects a test case, we let it pass
            return None

        self.exec("start")
        self.send_packets(pass_packets, pass_check_function, error_message)
        self.send_packets(fail_packets, fail_check_function, error_message)

    def do_test_with_expected_strings_for_pass_fail(self, rule: str, pass_packets: frozenset,
                                                    fail_packets: frozenset,
                                                    pass_expect: str, fail_expect: str, error_message: str):
        self.do_test_with_callable_tests_for_pass_fail(rule, pass_packets, fail_packets,
                                                       lambda output: pass_expect in output,
                                                       lambda output: fail_expect in output,
                                                       error_message)

    def do_test_with_queue_action(self, rule: str, pass_packets: frozenset, fail_packets: frozenset):
        self.do_test_with_expected_strings_for_pass_fail(rule, pass_packets, fail_packets,
                                                         f"port {self.dut_ports[0]}/queue 1",
                                                         f"port {self.dut_ports[0]}/queue 0",
                                                         "Error: packet went to the wrong queue")

    def set_up(self):
        """
        This is to clear up environment before the case run.
        """

    def tear_down(self):
        """
        Run after each test case.
        """
        self.exec(f"flow flush {self.dut_ports[0]}")
        self.exec("stop")

    def tear_down_all(self):
        """
        When the case of this test suite finished, the environment should
        clear up.
        """
        self.tester.send_expect("exit()", "#")
        self.dut.kill_all()
        self.tester.kill_all()

    """
    Edge Cases
    
    These are tests which are designed to deal with edge cases.
    """

    def test_excessive_voids(self):
        """
        This test puts far, far too many void tokens in an otherwise valid
        pattern. This may cause a crash or other issue, due to buffer size
        constraints or other limits inside of either the parser or the nic.
        """
        self.do_test_with_queue_action(
            "ingress pattern eth / ipv4 / " + (
                    "void / " * 200) + "udp / end actions queue index 1 / end",
            frozenset({'Ether() / IP() / UDP() / (\'\\x00\' * 64)'}),
            frozenset({
                'Ether() / IP() / TCP() / (\'\\x00\' * 64)',
                'Ether() / IP() / SCTP() / (\'\\x00\' * 64)',
                'Ether() / IPv6() / UDP() / (\'\\x00\' * 64)',
            })
        )

    def test_excessive_tunneling(self):
        self.do_test_with_queue_action(
            "ingress pattern " + ("eth / gre / " * 20) + "eth / ipv4 / udp / end actions queue index 1 / end",
            frozenset({'Ether() / IP() / UDP() / (\'\\x00\' * 64)'}),
            frozenset({
                'Ether() / IP() / TCP() / (\'\\x00\' * 64)',
                'Ether() / IP() / SCTP() / (\'\\x00\' * 64)',
                'Ether() / IPv6() / UDP() / (\'\\x00\' * 64)',
            })
        )

    """
    Action Test Cases
    
    These are test cases built for testing various actions
    """

    def test_drop_case1(self):
        self.do_test_with_callable_tests_for_pass_fail(
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions drop / end",
            frozenset({'Ether() / IP(src="192.168.0.1") / UDP() / (\'\\x00\' * 64)'}),
            frozenset({'Ether() / IP(src="10.0.30.99") / UDP() / (\'\\x00\' * 64)',
                       'Ether() / IP(src="132.177.0.99") / UDP() / (\'\\x00\' * 64)',
                       'Ether() / IP(src="192.168.0.2") / UDP() / (\'\\x00\' * 64)',
                       'Ether() / IP(src="8.8.8.8") / UDP() / (\'\\x00\' * 64)'}),
            lambda output: "port" not in output,
            lambda output: "port" in output,
            "Drop function was not correctly applied")

    def test_queue_case1(self):
        self.do_test_with_queue_action(
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions queue index 1 / end",
            frozenset({'Ether() / IP(src="192.168.0.1") / UDP() / (\'\\x00\' * 64)'}), frozenset(
                {'Ether() / IP(src="10.0.30.99") / UDP() / (\'\\x00\' * 64)',
                 'Ether() / IP(src="132.177.0.99") / UDP() / (\'\\x00\' * 64)',
                 'Ether() / IP(src="192.168.0.2") / UDP() / (\'\\x00\' * 64)',
                 'Ether() / IP(src="8.8.8.8") / UDP() / (\'\\x00\' * 64)'}))


def do_runtime_test_generation():
    """
    There are enough tests for this suite that it presents a maintainability
    issue to keep using the generator manually, so this approach is designed
    """
    print("Generating test cases for RTE Flow test suite.")
    pattern_functions = generator.create_test_function_strings(generator.get_patterns_with_properties())

    pattern_function_string = "\n".join(pattern_functions)
    exec(pattern_function_string)

    # Copy it because a for loop creates local variables, which changes the dict at runtime.
    locals_copy = filter(lambda name_function_tuple: name_function_tuple[0].startswith("test_"), locals().items())

    for name, function in locals_copy:
        setattr(RteFlow, name, function)


do_runtime_test_generation()
