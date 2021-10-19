# BSD LICENSE
#
# Copyright(c) 2016-2017 Intel Corporation. All rights reserved.
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


from framework.test_case import TestCase


class TestACL(TestCase):

    def install_acl_rules(self):
        # copy 'dep/test-acl-input.tar.gz' from tester to DUT,
        # and unpack the tarball into temporary directory.
        self.clean_acl_rules()
        self.dut.session.copy_file_to(f'dep/{self.acl_tarball}', '/tmp')
        self.dut.send_expect(f'tar xf /tmp/{self.acl_tarball} --directory=/tmp', '# ')


    def clean_acl_rules(self):
        # remove the temporary tarball file and directory
        self.dut.send_expect(f'rm -rf /tmp/{self.acl_tarball} {self.acl_rules_dir}', '# ', 20)


    def set_up_all(self):
        """
        Run once at the start of entire test suite.
        """
        # build ${DPDK}/<build>/app/dpdk-test-acl
        self.test_acl_sh = 'app/test-acl/test-acl.sh'
        out = self.dut.send_expect(f'ls -l {self.test_acl_sh}', '# ')
        self.logger.info(f'test_acl_sh: {self.test_acl_sh}')
        self.test_acl_bin = self.dut.apps_name['test-acl']
        self.logger.info(f'test_acl_app: {self.test_acl_bin}')

        # prepare test-acl-input directory
        self.acl_tarball = 'test-acl-input.tar.gz'
        self.acl_rules_dir = '/tmp/test-acl-input'
        self.install_acl_rules()


    def set_up(self):
        """
        Run before each test case.
        """
        pass


    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()


    def tear_down_all(self):
        """
        Run once after entire test suite.
        """
        self.clean_acl_rules()


    def run_test_acl(self, alg):
        # Example:
        # 	for j in scalar sse avx512x16 avx512x32
        # 	do
        # 		for i in 15 16 17 18 23 24 25 31 32 33 34 35 47 48 51 255 256 257
        # 		do
        # 			nohup /bin/bash -x ./ test-acl.sh \
        # 				./dpdk.org/x86_64-default-linuxapp-gcc-meson/app/dpdk-test-acl \
        # 				./test-pmac/classbench/dbs ${j} ${i}
        # 		done 2>&1 | tee test-acl.${j}.out
        # 	done
        # 	grep FAILED test-acl.*.out
        for burst_size in ('15', '16', '17', '18', '23', '24', '25', '31', '32', '33', '34', '35', '47', '48', '51', '255', '256', '257'):
            acl_test_cmd = f'/bin/bash -x {self.test_acl_sh} {self.test_acl_bin} {self.acl_rules_dir} {alg} {burst_size}'
            out = self.dut.send_expect(acl_test_cmd,  '# ', 1200, trim_whitespace=False)
            self.verify('FAILED' not in out, f'for details see TestACL.log')
        self.logger.info('All tests have ended successfully')


    def test_acl_scalar(self):
        self.run_test_acl('scalar')


    def test_acl_sse(self):
        self.run_test_acl('sse')


    def test_acl_avx2(self):
        self.run_test_acl('avx2')


    def test_acl_avx512x16(self):
        self.run_test_acl('avx512x16')


    def test_acl_avx512x32(self):
        self.run_test_acl('avx512x32')
