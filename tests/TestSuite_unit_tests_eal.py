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

EAL autotest.

"""

import framework.utils as utils
from framework.test_case import TestCase

#
#
# Test class.
#


class TestUnitTestsEal(TestCase):

    #
    #
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        # icc compilation cost long long time.
        [arch, machine, self.env, toolchain] = self.target.split('-')
        self.start_test_time = 60
        self.run_cmd_time = 180
        default_cores = '1S/4C/1T'
        eal_params = self.dut.create_eal_parameters(cores=default_cores)
        app_name = self.dut.apps_name['test']
        self.test_app_cmdline = app_name + eal_params

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_version(self):
        """
        Run version autotest.
        """

        self.dut.send_expect(self.dut.taskset(1) + ' ' + self.test_app_cmdline,
                             "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("version_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_memcopy(self):
        """
        Run memcopy autotest.
        """

        self.dut.send_expect(self.dut.taskset(1) + ' ' +  self.test_app_cmdline,
                             "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("memcpy_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_common(self):
        """
        Run common autotest.
        """

        self.dut.send_expect(self.dut.taskset(1) + ' ' + self.test_app_cmdline,
                             "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("common_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_eal_fs(self):
        """
        Run memcopy autotest.
        """

        self.dut.send_expect(self.dut.taskset(1) + ' ' + self.test_app_cmdline,
                             "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("eal_fs_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_memcpy(self):
        """
        Run memcopy autotest.
        """

        self.dut.send_expect(self.dut.taskset(1) + ' ' + self.test_app_cmdline,
                             "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("memcpy_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_memcpy_perf(self):
        """
        Run memcopy performance autotest.
        """
        self.dut.send_expect(self.dut.taskset(1) + ' ' + self.test_app_cmdline,
                             "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("memcpy_perf_autotest", "RTE>>", self.run_cmd_time * 15)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_hash(self):
        """
        Run hash autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("hash_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")

        # Extendable Bucket Table enhances and guarantees insertion of 100% of
        # the keys for a given hash table size. Add the check that average
        # table utilization is 100% when extendable table is enabled.

        self.verify("Average table utilization = 100.00%" in out,
                    "Test failed for extenable bucket table")
        self.verify("Test OK" in out, "Test failed")

    def test_hash_perf(self):
        """
        Run has performance autotest.
        """

        self.dut.send_expect(self.test_app_cmdline,
                             "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("hash_perf_autotest", "RTE>>", self.run_cmd_time * 10)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_hash_functions(self):
        """
        Run hash functions autotest.
        """

        self.dut.send_expect(self.test_app_cmdline,
                             "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("hash_functions_autotest",
                                   "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_hash_multiwriter(self):
        """
        Run hash multiwriter autotest.
        """

        self.dut.send_expect(self.test_app_cmdline,
                             "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("hash_multiwriter_autotest",
                                   "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_hash_readwrite(self):
        """
        Run hash readwrite autotest.
        """

        self.dut.send_expect(self.test_app_cmdline,
                             "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("hash_readwrite_func_autotest",
                                   "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_hash_readwrite_lf(self):
        """
        Run hash readwrite_lf autotest.
        """

        eal_params = self.dut.create_eal_parameters()
        self.dut.send_expect(self.test_app_cmdline,       
                             "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("hash_readwrite_lf_perf_autotest",
                                   "RTE>>", self.run_cmd_time*3)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_hash_readwrite_perf(self):
        """
        Run hash readwrite perf autotest.
        """

        eal_params = self.dut.create_eal_parameters(cores='1S/4C/1T')
        self.dut.send_expect(self.test_app_cmdline,
                             "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("hash_readwrite_perf_autotest",
                                   "RTE>>", self.run_cmd_time*3)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_func_reentrancy(self):
        """
        Run function reentrancy autotest.
        """

        if self.dut.architecture == "x86_64":
            cmdline = self.test_app_cmdline
        else:
            # mask cores only on socket 0
            app_name = self.dut.apps_name['test']
            cmdline = self.dut.taskset(1)+ ' ' +app_name+' -n 1 -c 5'            
        self.dut.send_expect(cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("func_reentrancy_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_atomic(self):
        """
        Run atomic autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("atomic_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_memory(self):
        """
        Run memory autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect('memory_autotest', "RTE>>", self.run_cmd_time * 5)
        regexp = "IOVA:0x[0-9a-f]*, len:([0-9a-f]*), virt:0x[0-9a-f]*, socket_id:[0-9]*"
        match = utils.regexp(out, regexp)
        size = int(match, 16)
        self.verify(size > 0, "bad size")
        self.dut.send_expect("quit", "# ")

    def test_lcore_launch(self):
        """
        Run lcore autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("per_lcore_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_spinlock(self):
        """
        Run spinlock autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("spinlock_autotest", "RTE>>", self.run_cmd_time * 2)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_prefetch(self):
        """
        Run prefetch autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("prefetch_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_byteorder(self):
        """
        Run byte order autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("byteorder_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_logs(self):
        """
        Run logs autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("logs_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_memzone(self):
        """
        Run memzone autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("memzone_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_debug(self):
        """
        Run debug autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("debug_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_cpuflags(self):
        """
        Run CPU flags autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("cpuflags_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_errno(self):
        """
        Run errno autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*TE>>|RT.*E>>|RTE.*>>|RTE>.*>", self.start_test_time)
        out = self.dut.send_expect("errno_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_interrupts(self):
        """
        Run interrupt autotest.
        """

        self.verify(self.env == "linuxapp", "Interrupt only supported in linux env")
        self.dut.send_expect(self.test_app_cmdline, "R.*TE>>|RT.*E>>|RTE.*>>|RTE>.*>", self.start_test_time)
        out = self.dut.send_expect("interrupt_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_multiprocess(self):
        """
        Run multiprocess autotest.
        """
        if self.dut.get_os_type() == "freebsd":
            self.dut.send_expect(self.test_app_cmdline + ' -m 64 --base-virtaddr=0x1000000000', "R.*T.*E.*>.*>", self.start_test_time)
        else:
            self.dut.send_expect(self.test_app_cmdline + ' -m 64', "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("multiprocess_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_string(self):
        """
        Run string autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("string_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_tailq(self):
        """
        Run tailq autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("tailq_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_kvargs(self):
        """
        Run kvargs autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("kvargs_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_acl(self):
        """
        Run acl autotest.
        """
        eal_params = self.dut.create_eal_parameters(other_eal_param='force-max-simd-bitwidth')
        app_name = self.dut.apps_name['test']
        test_app_cmdline = app_name + eal_params
        test_app_cmdline += "--no-pci"

        if self.dut.dpdk_version >= '20.11.0':
            test_app_cmdline += " --force-max-simd-bitwidth=0"
        self.dut.send_expect(test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("acl_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_link_bonding(self):
        """
        Run acl autotest.
        """

        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("link_bonding_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_link_bonding_rssconf(self):
        """
        """
        self.dut.send_expect(self.test_app_cmdline, "R.*T.*E.*>.*>", self.start_test_time)
        out = self.dut.send_expect("link_bonding_rssconf_autotest", "RTE>>", self.run_cmd_time)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
