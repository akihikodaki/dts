# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
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

import re

"""
DPDK Test suite.

Run Inter-VM share memory autotests
"""


import framework.utils as utils
from framework.test_case import TestCase

#
#
# Test class.
#


class TestUnitTestsDump(TestCase):

    #
    #
    #
    # Test cases.
    #


    def set_up_all(self):
        """
        Run at the start of each test suite.
        Nothing to do here.
        """
        # Based on h/w type, choose how many ports to use
        self.cores = self.dut.get_core_list("all")
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.start_test_time = 60
        self.run_cmd_time = 60

    def set_up(self):
        """
        Run before each test case.
        Nothing to do here.
        """
        pass

    def discard_test_log_dump(self):
        """
        Run history log dump test case.
        """
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name['test']
        self.dut.send_expect(app_name + eal_params,"R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("dump_log_history", "RTE>>", self.run_cmd_time * 2)
        self.dut.send_expect("quit", "# ")
        self.verify("EAL" in out, "Test failed")

    def test_ring_dump(self):
        """
        Run history log dump test case.
        """
        eal_params = self.dut.create_eal_parameters(cores='1S/4C/1T')
        cmd = self.dut.apps_name['test-pmd'] + eal_params + '-- -i'        

        self.dut.send_expect("%s" % cmd, "testpmd>", self.start_test_time)
        out = self.dut.send_expect("dump_ring", "testpmd>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        match_regex = "ring <(.*?)>"
        m = re.compile(r"%s" % match_regex, re.S)
        results = m.findall(out)
        
        # Nic driver will create multiple rings.
        # Only check the last one to make sure ring_dump function work.
        self.verify( 'MP_mb_pool_0' in results, "dump ring name failed")
        for result in results:
            self.dut.send_expect("%s" % cmd, "testpmd>", self.start_test_time)
            out = self.dut.send_expect("dump_ring %s" % result, "testpmd>", self.run_cmd_time)
            self.dut.send_expect("quit", "# ")
            self.verify( 'capacity' in out, "dump ring name failed")

    def test_mempool_dump(self):
        """
        Run mempool dump test case.
        """
        eal_params = self.dut.create_eal_parameters(cores='1S/4C/1T')
        cmd = self.dut.apps_name['test-pmd'] + eal_params + '-- -i'

        self.dut.send_expect("%s" % cmd, "testpmd>", self.start_test_time)
        out = self.dut.send_expect("dump_mempool", "testpmd>", self.run_cmd_time * 2)
        self.dut.send_expect("quit", "# ")
        match_regex = "mempool <(.*?)>@0x(.*?)\r\n"
        m = re.compile(r"%s" % match_regex, re.S)
        results = m.findall(out)

        self.verify(results[0][0] == 'mb_pool_0', "dump mempool name failed")
        for result in results:
            self.dut.send_expect("%s" % cmd, "testpmd>", self.start_test_time)
            out = self.dut.send_expect("dump_mempool %s" % result[0], "testpmd>", self.run_cmd_time * 2)
            self.dut.send_expect("quit", "# ")
            self.verify("internal cache infos:" in out, "dump mempool name failed")


    def test_physmem_dump(self):
        """
        Run physical memory dump test case.
        """
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name['test']
        self.dut.send_expect(app_name + eal_params,"R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("dump_physmem", "RTE>>", self.run_cmd_time * 2)
        self.dut.send_expect("quit", "# ")
        elements = ['Segment', 'IOVA', 'len', 'virt', 'socket_id', 'hugepage_sz', 'nchannel', 'nrank']
        match_regex = "Segment (.*?):"
        for element in elements[1:-1]:
            match_regex += " %s:(.*?)," % element
        match_regex += " %s:(.*?)" % elements[-1]
        m = re.compile(r"%s" % match_regex, re.DOTALL)
        results = m.findall(out)
        phy_info = []
        for result in results:
            phy_info.append(dict(list(zip(elements, result))))

        self.verify(len(phy_info) > 0, "Test failed")

    def test_memzone_dump(self):
        """
        Run memzone dump test case.
        """
        eal_params = self.dut.create_eal_parameters(cores='1S/4C/1T')
        cmd = self.dut.apps_name['test-pmd'] + eal_params + '-- -i'

        self.dut.send_expect("%s" % cmd, "testpmd>", self.start_test_time)
        out = self.dut.send_expect("dump_memzone", "testpmd>", self.run_cmd_time * 2)
        self.dut.send_expect("quit", "# ")

        elements = ['Zone', 'name', 'len', 'virt', 'socket_id', 'flags']
        match_regex = "Zone (\d):"
        for element in elements[1:-1]:
            match_regex += " %s:(.*?)," % element
        match_regex += " %s:(.*?)\n" % elements[-1]
        m = re.compile(r"%s" % match_regex, re.DOTALL)
        results = m.findall(out)
        memzone_info = []
        for result in results:
            memzone_info.append(dict(list(zip(elements, result))))

        self.verify(len(memzone_info) > 0, "Test failed")

    def test_dump_struct_size(self):
        """
        Run struct size dump test case.
        """
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name['test']
        self.dut.send_expect(app_name + eal_params,"R.*T.*E.*>.*>", self.start_test_time)       
        out = self.dut.send_expect("dump_struct_sizes", "RTE>>", self.run_cmd_time * 2)
        self.dut.send_expect("quit", "# ")

        elements = ['struct rte_mbuf', 'struct rte_mempool', 'struct rte_ring']
        match_regex = ""
        for element in elements[:-1]:
            match_regex += "sizeof\(%s\) = (\d+)\r\n" % element
        match_regex += "sizeof\(%s\) = (\d+)" % elements[-1]
        m = re.compile(r"%s" % match_regex, re.S)

        result = m.search(out)
        struct_info = dict(list(zip(elements, result.groups())))

    def test_dump_devargs(self):
        """
        Run devargs dump test case.
        """
        test_port = self.dut_ports[0]
        pci_address = self.dut.ports_info[test_port]['pci'];
        eal_params = self.dut.create_eal_parameters(cores=self.cores,b_ports=[pci_address])
        app_name = self.dut.apps_name['test']
        self.dut.send_expect(app_name + eal_params,"R.*T.*E.*>.*>", self.start_test_time)       
        out = self.dut.send_expect("dump_devargs", "RTE>>", self.run_cmd_time * 2)
        self.dut.send_expect("quit", "# ")
        block_str = " %s" % pci_address
        self.verify(block_str in out, "Dump block list failed")

        eal_params1 = self.dut.create_eal_parameters(cores=self.cores,ports=[pci_address])
        app_name = self.dut.apps_name['test']
        self.dut.send_expect(app_name + eal_params1,"R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("dump_devargs", "RTE>>", self.run_cmd_time * 2)
        self.dut.send_expect("quit", "# ")

        allow_str = "[pci]: %s" % pci_address
        self.verify(allow_str in out, "Dump allow list failed")

    def test_dump_malloc_stats(self):
        """
        Run dump malloc dump test case.
        """
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name['test']
        self.dut.send_expect(app_name + eal_params,"R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("dump_malloc_stats", "RTE>>", self.run_cmd_time * 2)
        self.dut.send_expect("quit", "# ")
        match_regex = "Heap id:(\d*)"
        m = re.compile(r"%s" % match_regex, re.DOTALL)
        results = m.findall(out)
        memzone_info = []
        for result in results:
            memzone_info.append(result)
        self.verify(len(memzone_info) > 0, "Dump malloc stats failed")

    def test_dump_malloc_heaps(self):
        """
        Run malloc heaps dump test case.
        """
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name['test']
        self.dut.send_expect(app_name + eal_params,"R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("dump_malloc_heaps", "RTE>>", self.run_cmd_time * 2)
        self.dut.send_expect("quit", "# ")

        elements = ['Heap id', 'Heap size', 'Heap alloc count']
        match_regex = ""
        for element in elements:
            match_regex += "%s:(.*?)\r\n" % element
        m = re.compile(r"%s" % match_regex, re.DOTALL)
        results = m.findall(out)
        memzone_info = []
        for result in results:
            memzone_info.append(dict(list(zip(elements, result))))
        self.verify(len(memzone_info) > 0, "Dump malloc heaps failed")

    def test_dump_log_types(self):
        """
        Run log types dump test case.
        """
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name['test']
        self.dut.send_expect(app_name + eal_params,"R.*T.*E.*>.*>", self.start_test_time)        
        out = self.dut.send_expect("dump_log_types", "RTE>>", self.run_cmd_time * 2)
        self.dut.send_expect("quit", "# ")

        elements = ['id']
        match_regex = "id (\d):"
        match_regex += "(.*?),"
        m = re.compile(r"%s" % match_regex, re.DOTALL)
        results = m.findall(out)
        memzone_info = []
        for result in results:
            memzone_info.append(dict(list(zip(elements, result))))
        self.verify(len(memzone_info) > 0, "Dump log types failed")

    def tear_down(self):
        """
        Run after each test case.
        Stop application test after every case.
        """
        self.dut.kill_all()
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        Nothing to do here.
        """
        pass
