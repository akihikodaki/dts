# BSD LICENSE
#
# Copyright(c)2021 Intel Corporation. All rights reserved.
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
import time

from framework.settings import HEADER_SIZE

JUMBO_FRAME_MTU = 9600
DEFAULT_MTU_VALUE = 1500
COMMON_PKT_LEN = 64
JUMBO_FRAME_LENGTH = 9000
IPV4_SRC = '192.168.0.11'
IPV4_DST = '192.168.0.12'
LAUNCH_QUEUE = 4
PACKAGE_COUNT = 32


class SmokeTest(object):
    def __init__(self, test_case, **kwargs):
        self.test_case = test_case
        for name in kwargs:
            setattr(self, name, kwargs[name])

    def send_pkg_return_stats(self, pkt_size=COMMON_PKT_LEN, l3_src=IPV4_SRC, l3_dst=IPV4_DST, rss=False):
        self.test_case.dut.send_expect("clear port stats all", "testpmd> ")
        l3_len = pkt_size - HEADER_SIZE['eth']
        payload = pkt_size - HEADER_SIZE['eth'] - HEADER_SIZE['ip']
        hash_flag = False
        if rss:
            pkt = []
            # generate PACKAGE_COUNT count package, the IP dst is random.
            for i in range(0, PACKAGE_COUNT):
                p = "Ether(dst='{}',src='{}')/IP(src='{}',dst=RandIP(),len={})/Raw(load='X'*{})".format(
                    self.test_case.smoke_dut_mac,
                    self.test_case.smoke_tester_mac,
                    l3_src,
                    l3_len,
                    payload)
                pkt.append(p)
        else:
            pkt = ["Ether(dst='{}',src='{}')/IP(src='{}',dst='{}',len={})/Raw(load='X'*{})".format(
                self.test_case.smoke_dut_mac,
                self.test_case.smoke_tester_mac,
                l3_src,
                l3_dst,
                l3_len,
                payload)]

        self.test_case.pkt.update_pkt(pkt)

        # wait package update
        time.sleep(1)
        self.test_case.pkt.send_pkt(crb=self.test_case.tester, tx_port=self.test_case.smoke_tester_nic)
        time.sleep(.5)
        out = self.test_case.pmd_out.get_output(timeout=1)
        queue_pattern = re.compile(r'Receive\squeue=(\w+)')
        # collect all queues
        queues = queue_pattern.findall(out)
        # get dpdk statistical information
        stats = self.test_case.pmd_out.get_pmd_stats(self.test_case.smoke_dut_ports[0])
        if 'RTE_MBUF_F_RX_RSS_HASH' in out:
            hash_flag = True

        if rss:
            rss_pattern = re.compile(r'-\sRSS\shash=(\w+)')
            # collect all hash value
            rss_hash = rss_pattern.findall(out)
            if 0 != len(rss_hash):
                return hash_flag, queues, rss_hash
            else:
                if 0 != len(queues):
                    return hash_flag, queues, None
                else:
                    return hash_flag, None, None
        if 0 != len(queues):
            return queues[0], stats
        return None, stats

    def check_jumbo_frames(self):
        """
        The packet total size include ethernet header, ip header, and payload.
        ethernet header length is 18 bytes, ip standard header length is 20 bytes.
        The packet forwarded failed.
        """
        pkg_size = JUMBO_FRAME_LENGTH + 1
        queues, stats = self.send_pkg_return_stats(pkg_size)
        if 1 != stats['RX-errors'] and 0 != stats['TX-packets']:
            self.test_case.logger.info("jumbo frame: The RX[{}] or TX[{}] packet error".format(stats['RX-errors'],
                                                                                               stats['TX-packets']))
            return False

        # The packet can be forwarded successfully.
        pkg_size = JUMBO_FRAME_LENGTH
        queues, stats = self.send_pkg_return_stats(pkg_size)
        if 1 != stats['TX-packets']:
            self.test_case.logger.info("jumbo frame: The TX[{}] packet error".format(stats['TX-packets']))
            return False

        return True

    def check_rss(self):
        """
        Test the basic functions of RSS, every queue can receive packets.
        """
        hash_flag, queues, hash_values = self.send_pkg_return_stats(rss=True)
        if queues is None or hash_values is None:
            return False
        queues = list(set(queues))
        hash_values = list(set(hash_values))

        # verify that each queue has packets, verify hash value are not equal, and hash flag exists.
        if LAUNCH_QUEUE != len(queues) or 1 == hash_values or hash_flag is False:
            self.test_case.logger.info("rss the hash flag [{}] [{}] error".format(queues, hash_values))
            return False

        return True

    def check_tx_rx_queue(self):
        """
        Test configuration queue function can work.
        """
        # verify default configure can work
        queues, stats = self.send_pkg_return_stats()
        if queues is None:
            self.test_case.logger.info("txq rxq the queues[{}] error".format(queues))
            return False

        self.test_case.dut.send_expect("stop", "testpmd> ")
        self.test_case.dut.send_expect("port stop all", "testpmd> ")
        self.test_case.dut.send_expect("port config all rxq 1", "testpmd> ")
        self.test_case.dut.send_expect("port config all txq 1", "testpmd> ")
        out = self.test_case.dut.send_expect("show config rxtx", "testpmd> ")
        if 'RX queue number: 1' not in out:
            self.test_case.logger.info("RX queue number 1 no display")
            return False
        if 'Tx queue number: 1' not in out:
            self.test_case.logger.info("Tx queue number 1 no display")
            return False

        self.test_case.dut.send_expect("port start all", "testpmd> ")
        self.test_case.dut.send_expect("start", "testpmd> ")
        self.test_case.pmd_out.wait_link_status_up(self.test_case.smoke_dut_ports[0])
        queue_after, stats = self.send_pkg_return_stats()

        if queue_after is None:
            self.test_case.logger.info("after txq rxq the queue [{}] error".format(queue_after))
            return False

        return True
