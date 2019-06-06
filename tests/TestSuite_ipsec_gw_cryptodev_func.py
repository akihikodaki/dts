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

import hmac
import hashlib
import binascii
import time
import utils
from test_case import TestCase
from packet import Packet, save_packets

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESCCM, AESGCM
from cryptography.hazmat.backends import default_backend

import cryptodev_common as cc

class TestIPsecGW(TestCase):

    def set_up_all(self):

        self.core_config = "1S/2C/1T"
        self.number_of_ports = 1
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= self.number_of_ports,
                    "Not enough ports for " + self.nic)
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])

        self.logger.info("core config = " + self.core_config)
        self.logger.info("number of ports = " + str(self.number_of_ports))
        self.logger.info("dut ports = " + str(self.dut_ports))
        self.logger.info("ports_socket = " + str(self.ports_socket))

        # Generally, testbed should has 4 ports NIC, like,
        # 03:00.0 03:00.1 03:00.2 03:00.3
        # This test case will
        # - physical link is 03:00.0 <-> 03:00.1 and 03:00.2 <-> 03:00.3
        # - bind 03:00.0 and 03:00.2 to ipsec-secgw app
        # - send test packet from 03:00.3
        # - receive packet which forwarded by ipsec-secgw from 03:00.0
        # - configure port and peer in dts port.cfg
        self.tx_port = self.tester.get_local_port(self.dut_ports[1])
        self.rx_port = self.tester.get_local_port(self.dut_ports[0])

        self.tx_interface = self.tester.get_interface(self.tx_port)
        self.rx_interface = self.tester.get_interface(self.rx_port)

        self.logger.info("tx interface = " + self.tx_interface)
        self.logger.info("rx interface = " + self.rx_interface)

        self._app_path = "./examples/ipsec-secgw/build/ipsec-secgw"
        if not cc.is_build_skip(self):
            cc.build_dpdk_with_cryptodev(self)
        out =self.dut.build_dpdk_apps("./examples/ipsec-secgw")
        self.verify("Error"not in out,"Compilation error")
        self.verify("No such"not in out,"Compilation error")
        self.vf_driver = self.get_suite_cfg()['vf_driver']
        cc.bind_qat_device(self, self.vf_driver)

        self._default_ipsec_gw_opts = {
            "config": None,
            "P": "",
            "p": "0x3",
            "f": "local_conf/ipsec_test.cfg",
            "u": "0x1"
        }

        self._pcap_idx = 0
        self.pcap_filename = ''

    def set_up(self):
        pass

    def tear_down(self):
        self.dut.kill_all()

    def tear_down_all(self):
        cc.clear_dpdk_config(self)

    def test_qat_aes_128_cbc_ipv4_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_128_cbc_ipv4_tunnel")
        self.pcap_filename = "test_qat_aes_128_cbc_ipv4_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_qat_aes_256_cbc_ipv4_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_256_cbc_ipv4_tunnel")
        self.pcap_filename = "test_qat_aes_256_cbc_ipv4_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_qat_aes_gcm_ipv4_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_gcm_ipv4_tunnel")
        self.pcap_filename = "test_qat_aes_gcm_ipv4_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)
        self.verify(result, "FAIL")

    def test_qat_aes_128_ctr_ipv4_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_128_ctr_ipv4_tunnel")
        self.pcap_filename = "test_qat_aes_128_ctr_ipv4_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)
        self.verify(result, "FAIL")

    def test_qat_aes_128_ctr_ipv6_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_128_ctr_ipv6_tunnel")
        self.pcap_filename = "test_qat_aes_128_ctr_ipv6_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)
        self.verify(result, "FAIL")

    def test_qat_aes_128_ctr_ipv4_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_128_ctr_ipv4_transport")
        self.pcap_filename = "test_qat_aes_128_ctr_ipv4_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)
        self.verify(result, "FAIL")

    def test_qat_aes_128_ctr_ipv6_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_128_ctr_ipv6_transport")
        self.pcap_filename = "test_qat_aes_128_ctr_ipv6_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)
        self.verify(result, "FAIL")

    def test_qat_null_ipv4_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_null_ipv4_tunnel")
        self.pcap_filename = "test_qat_null_ipv4_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_qat_aes_128_cbc_ipv4_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_128_cbc_ipv4_transport")
        self.pcap_filename = "test_qat_aes_128_cbc_ipv4_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_qat_aes_256_cbc_ipv4_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_256_cbc_ipv4_transport")
        self.pcap_filename = "test_qat_aes_256_cbc_ipv4_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_qat_aes_gcm_ipv4_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_gcm_ipv4_transport")
        self.pcap_filename = "test_qat_aes_gcm_ipv4_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)
        self.verify(result, "FAIL")

    def test_qat_aes_128_cbc_ipv6_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_128_cbc_ipv6_tunnel")
        self.pcap_filename = "test_qat_aes_128_cbc_ipv6_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_qat_aes_256_cbc_ipv6_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_256_cbc_ipv6_tunnel")
        self.pcap_filename = "test_qat_aes_256_cbc_ipv6_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_qat_aes_gcm_ipv6_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_gcm_ipv6_tunnel")
        self.pcap_filename = "test_qat_aes_gcm_ipv6_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_qat_null_ipv6_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_null_ipv6_tunnel")
        self.pcap_filename = "test_qat_null_ipv6_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_qat_aes_128_cbc_ipv6_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_128_cbc_ipv6_transport")
        self.pcap_filename = "test_qat_aes_128_cbc_ipv6_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_qat_aes_256_cbc_ipv6_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_256_cbc_ipv6_transport")
        self.pcap_filename = "test_qat_aes_256_cbc_ipv6_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_qat_aes_gcm_ipv6_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test qat_aes_gcm_ipv6_transport")
        self.pcap_filename = "test_qat_aes_gcm_ipv6_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)
        self.verify(result, "FAIL")

    def test_sw_aes_128_cbc_ipv4_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_128_cbc_ipv4_tunnel")
        self.pcap_filename = "test_sw_aes_128_cbc_ipv4_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_sw_aes_256_cbc_ipv4_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_256_cbc_ipv4_tunnel")
        self.pcap_filename = "test_sw_aes_256_cbc_ipv4_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_sw_aes_gcm_ipv4_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_gcm_ipv4_tunnel")
        self.pcap_filename = "test_sw_aes_gcm_ipv4_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)
        self.verify(result, "FAIL")

    def test_sw_null_ipv4_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_null_ipv4_tunnel")
        self.pcap_filename = "test_sw_null_ipv4_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_sw_aes_128_cbc_ipv4_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_128_cbc_ipv4_transport")
        self.pcap_filename = "test_sw_aes_128_cbc_ipv4_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_sw_aes_256_cbc_ipv4_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_256_cbc_ipv4_transport")
        self.pcap_filename = "test_sw_aes_256_cbc_ipv4_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_sw_aes_gcm_ipv4_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_gcm_ipv4_transport")
        self.pcap_filename = "test_sw_aes_gcm_ipv4_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)
        self.verify(result, "FAIL")

    def test_sw_aes_128_cbc_ipv6_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_128_cbc_ipv6_tunnel")
        self.pcap_filename = "test_sw_aes_128_cbc_ipv6_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_sw_aes_256_cbc_ipv6_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_256_cbc_ipv6_tunnel")
        self.pcap_filename = "test_sw_aes_256_cbc_ipv6_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_sw_aes_gcm_ipv6_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_gcm_ipv6_tunnel")
        self.pcap_filename = "test_sw_aes_gcm_ipv6_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_sw_null_ipv6_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_null_ipv6_tunnel")
        self.pcap_filename = "test_sw_null_ipv6_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_sw_aes_128_cbc_ipv6_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_128_cbc_ipv6_transport")
        self.pcap_filename = "test_sw_aes_128_cbc_ipv6_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_sw_aes_256_cbc_ipv6_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_256_cbc_ipv6_transport")
        self.pcap_filename = "test_sw_aes_256_cbc_ipv6_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)

        self.verify(result, "FAIL")

    def test_sw_aes_gcm_ipv6_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_gcm_ipv6_transport")
        self.pcap_filename = "test_sw_aes_gcm_ipv6_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)
        self.verify(result, "FAIL")

    def test_sw_aes_128_ctr_ipv4_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_128_ctr_ipv4_tunnel")
        self.pcap_filename = "test_sw_aes_128_ctr_ipv4_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)
        self.verify(result, "FAIL")

    def test_sw_aes_128_ctr_ipv6_tunnel(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_128_ctr_ipv6_tunnel")
        self.pcap_filename = "test_sw_aes_128_ctr_ipv6_tunnel"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)
        self.verify(result, "FAIL")

    def test_sw_aes_128_ctr_ipv4_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_128_ctr_ipv4_transport")
        self.pcap_filename = "test_sw_aes_128_ctr_ipv4_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)
        self.verify(result, "FAIL")

    def test_sw_aes_128_ctr_ipv6_transport(self):
        if cc.is_test_skip(self):
            return

        self.logger.info("Test sw_aes_128_ctr_ipv6_transport")
        self.pcap_filename = "test_sw_aes_128_ctr_ipv6_transport"
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()
        self.logger.debug(ipsec_gw_opt_str)

        result = self._execute_ipsec_gw_test(ipsec_gw_opt_str)
        self.verify(result, "FAIL")

    def _get_ipsec_gw_opt_str(self, override_ipsec_gw_opts={}):
        return cc.get_opt_str(self, self._default_ipsec_gw_opts,
                              override_ipsec_gw_opts)

    def _execute_ipsec_gw_test(self, ipsec_gw_opt_str):
        result = True
        eal_opt_str = cc.get_eal_opt_str(self, add_port=True)

        cmd_str = cc.get_dpdk_app_cmd_str(self._app_path, eal_opt_str, ipsec_gw_opt_str)
        self.logger.info("IPsec-gw cmd: " + cmd_str)
        self.dut.send_expect(cmd_str, "IPSEC:", 30)
        time.sleep(3)
        inst = self.tester.tcpdump_sniff_packets(self.rx_interface, timeout=25)

        PACKET_COUNT = 65
        payload = 256 * ['11']

        case_cfgs = self.get_case_cfg()
        dst_ip = case_cfgs["dst_ip"]
        src_ip = case_cfgs["src_ip"]
        expected_dst_ip = case_cfgs["expected_dst_ip"]
        expected_src_ip = case_cfgs["expected_src_ip"]
        expected_spi = case_cfgs["expected_spi"]
        expected_length = case_cfgs["expected_length"]
        #expected_data = case_cfgs["expected_data"]

        pkt = Packet()
        if len(dst_ip)<=15:
            pkt.assign_layers(["ether", "ipv4", "udp", "raw"])
            pkt.config_layer("ether", {"src": "52:00:00:00:00:00", "dst": "52:00:00:00:00:01"})
            pkt.config_layer("ipv4", {"src": src_ip, "dst": dst_ip})
        else:
            pkt.assign_layers(["ether", "ipv6", "udp", "raw"])
            pkt.config_layer("ether", {"src": "52:00:00:00:00:00", "dst": "52:00:00:00:00:01"})
            pkt.config_layer("ipv6", {"src": src_ip, "dst": dst_ip})
        pkt.config_layer("udp", {"dst": 0})
        pkt.config_layer("raw", {"payload": payload})
        pkt.send_pkt(tx_port=self.tx_interface, count=PACKET_COUNT)

        pkt_rec = self.tester.load_tcpdump_sniff_packets(inst)

        pcap_filename = "output/{0}.pcap".format(self.pcap_filename)
        self.logger.info("Save pkts to {0}".format(pcap_filename))
        save_packets(pkt_rec, pcap_filename)
        self._pcap_idx = self._pcap_idx + 1

        if len(pkt_rec) == 0:
            self.logger.error("IPsec forwarding failed")
            result = False

        for pkt_r in pkt_rec:
            pkt_src_ip = pkt_r.pktgen.strip_layer3("src")
            if pkt_src_ip != expected_src_ip:
                pkt_r.pktgen.pkt.show()
                self.logger.error("SRC IP does not match. Pkt:{0}, Expected:{1}".format(
                                   pkt_src_ip, expected_src_ip))
                result = False
                break

            pkt_dst_ip = pkt_r.pktgen.strip_layer3("dst")
            self.logger.debug(pkt_dst_ip)
            if pkt_dst_ip != expected_dst_ip:
                pkt_r.pktgen.pkt.show()
                self.logger.error("DST IP does not match. Pkt:{0}, Expected:{1}".format(
                                  pkt_dst_ip, expected_dst_ip))
                result = False
                break

            packet_hex = pkt_r.pktgen.pkt["ESP"].getfieldval("data")
            if packet_hex is None:
                self.logger.error("NO Payload !")
                result = False
                break
            payload_str = binascii.b2a_hex(packet_hex)
            self.logger.debug(payload_str)

            pkt_spi = hex(pkt_r.pktgen.pkt["ESP"].getfieldval("spi"))
            self.logger.debug(pkt_spi)
            if pkt_spi != expected_spi:
                self.logger.error("SPI does not match. Pkt:{0}, Expected:{1}".format(
                                  pkt_spi, expected_spi))
                result = False
                break

            pkt_len = len(payload_str)/2
            self.logger.debug(pkt_len)
            if pkt_len != int(expected_length):
                self.logger.error("Packet length does not match. Pkt:{0}, Expected:{1}".format(
                    pkt_len, expected_length))
                result = False
                break

        self.dut.kill_all()
        return result
