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

import binascii
import os.path
import time

import framework.packet as packet
import framework.utils as utils
import tests.cryptodev_common as cc
from framework.settings import CONFIG_ROOT_PATH
from framework.test_case import TestCase


class TestIPsecGW(TestCase):
    def set_up_all(self):
        self.core_config = "1S/3C/1T"
        self.number_of_ports = 2
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(
            len(self.dut_ports) >= self.number_of_ports,
            "Not enough ports for " + self.nic,
        )
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket
        )

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

        self._app_path = self.dut.apps_name["ipsec-secgw"]
        out = self.dut.build_dpdk_apps("./examples/ipsec-secgw")
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")

        cc.bind_qat_device(self, self.drivername)

        self._default_ipsec_gw_opts = {
            "config": '"(0,0,%s),(1,0,%s)"' % tuple(self.core_list[-2:]),
            "P": "",
            "p": "0x3",
            "f": "/tmp/ipsec_ep0.cfg",
            "u": "0x1",
        }

        conf_file = os.path.join(CONFIG_ROOT_PATH, "ipsec_ep0.cfg")
        self.dut.session.copy_file_to(conf_file, "/tmp")

    def set_up(self):
        pass

    def tear_down(self):
        self.dut.kill_all()

    def tear_down_all(self):
        pass

    def test_qat_aes_128_cbc_ipv4_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_qat_aes_256_cbc_ipv4_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_qat_aes_gcm_ipv4_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_qat_aes_128_ctr_ipv4_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_qat_aes_128_ctr_ipv6_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_qat_aes_128_ctr_ipv4_transport(self):
        self._execute_ipsec_gw_test()

    def test_qat_aes_128_ctr_ipv6_transport(self):
        self._execute_ipsec_gw_test()

    def test_qat_null_ipv4_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_qat_aes_128_cbc_ipv4_transport(self):
        self._execute_ipsec_gw_test()

    def test_qat_aes_256_cbc_ipv4_transport(self):
        self._execute_ipsec_gw_test()

    def test_qat_aes_gcm_ipv4_transport(self):
        self._execute_ipsec_gw_test()

    def test_qat_null_ipv4_transport(self):
        self._execute_ipsec_gw_test()

    def test_qat_aes_128_cbc_ipv6_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_qat_aes_256_cbc_ipv6_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_qat_aes_gcm_ipv6_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_qat_null_ipv6_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_qat_aes_128_cbc_ipv6_transport(self):
        self._execute_ipsec_gw_test()

    def test_qat_aes_256_cbc_ipv6_transport(self):
        self._execute_ipsec_gw_test()

    def test_qat_aes_gcm_ipv6_transport(self):
        self._execute_ipsec_gw_test()

    def test_qat_null_ipv6_transport(self):
        self._execute_ipsec_gw_test()

    def test_qat_3des_cbc_ipv4_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_qat_3des_cbc_ipv6_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_qat_3des_cbc_ipv4_transport(self):
        self._execute_ipsec_gw_test()

    def test_qat_3des_cbc_ipv6_transport(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_128_cbc_ipv4_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_256_cbc_ipv4_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_gcm_ipv4_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_sw_null_ipv4_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_128_cbc_ipv4_transport(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_256_cbc_ipv4_transport(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_gcm_ipv4_transport(self):
        self._execute_ipsec_gw_test()

    def test_sw_null_ipv4_transport(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_128_cbc_ipv6_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_256_cbc_ipv6_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_gcm_ipv6_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_sw_null_ipv6_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_128_cbc_ipv6_transport(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_256_cbc_ipv6_transport(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_gcm_ipv6_transport(self):
        self._execute_ipsec_gw_test()

    def test_sw_null_ipv6_transport(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_128_ctr_ipv4_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_128_ctr_ipv6_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_128_ctr_ipv4_transport(self):
        self._execute_ipsec_gw_test()

    def test_sw_aes_128_ctr_ipv6_transport(self):
        self._execute_ipsec_gw_test()

    def test_sw_3des_cbc_ipv4_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_sw_3des_cbc_ipv6_tunnel(self):
        self._execute_ipsec_gw_test()

    def test_sw_3des_cbc_ipv4_transport(self):
        self._execute_ipsec_gw_test()

    def test_sw_3des_cbc_ipv6_transport(self):
        self._execute_ipsec_gw_test()

    def _get_crypto_device(self, num):
        device = {}
        if self.get_case_cfg()["devtype"] == "crypto_aesni_mb":
            dev = "crypto_aesni_mb"
        elif self.get_case_cfg()["devtype"] == "crypto_qat":
            w = cc.get_qat_devices(self, cpm_num=1, num=num)
            device["a"] = " -a ".join(w)
            device["vdev"] = None
        elif self.get_case_cfg()["devtype"] == "crypto_openssl":
            dev = "crypto_openssl"
        elif self.get_case_cfg()["devtype"] == "crypto_aesni_gcm":
            dev = "crypto_aesni_gcm"
        elif self.get_case_cfg()["devtype"] == "crypto_kasumi":
            dev = "crypto_kasumi"
        elif self.get_case_cfg()["devtype"] == "crypto_snow3g":
            dev = "crypto_snow3g"
        elif self.get_case_cfg()["devtype"] == "crypto_zuc":
            dev = "crypto_zuc"
        elif self.get_case_cfg()["devtype"] == "crypto_null":
            dev = "crypto_null"
        else:
            return {}

        if not device:
            vdev_list = []
            for i in range(num):
                vdev = "{}{}".format(dev, i)
                vdev_list.append(vdev)
            device["a"] = "0000:00:00.0"
            device["vdev"] = " --vdev ".join(vdev_list)

        return device

    def _get_ipsec_gw_opt_str(self, override_ipsec_gw_opts={}):
        if (
            "librte_ipsec" in list(self.get_suite_cfg().keys())
            and self.get_suite_cfg()["librte_ipsec"]
        ):
            override_ipsec_gw_opts = {"l": ""}
        return cc.get_opt_str(self, self._default_ipsec_gw_opts, override_ipsec_gw_opts)

    def _execute_ipsec_gw_test(self):
        if cc.is_test_skip(self):
            return

        result = True
        opts = {"l": ",".join(self.core_list)}
        devices = self._get_crypto_device(self.number_of_ports)
        opts.update(devices)
        eal_opt_str = cc.get_eal_opt_str(self, opts, add_port=True)
        ipsec_gw_opt_str = self._get_ipsec_gw_opt_str()

        cmd_str = cc.get_dpdk_app_cmd_str(self._app_path, eal_opt_str, ipsec_gw_opt_str)
        self.dut.send_expect(cmd_str, "IPSEC:", 30)
        time.sleep(3)
        inst = self.tester.tcpdump_sniff_packets(self.rx_interface)

        PACKET_COUNT = 65
        payload = 256 * ["11"]

        case_cfgs = self.get_case_cfg()
        dst_ip = case_cfgs["dst_ip"]
        src_ip = case_cfgs["src_ip"]
        expected_dst_ip = case_cfgs["expected_dst_ip"]
        expected_src_ip = case_cfgs["expected_src_ip"]
        expected_spi = case_cfgs["expected_spi"]

        pkt = packet.Packet()
        if len(dst_ip) <= 15:
            pkt.assign_layers(["ether", "ipv4", "udp", "raw"])
            pkt.config_layer(
                "ether", {"src": "52:00:00:00:00:00", "dst": "52:00:00:00:00:01"}
            )
            pkt.config_layer("ipv4", {"src": src_ip, "dst": dst_ip})
        else:
            pkt.assign_layers(["ether", "ipv6", "udp", "raw"])
            pkt.config_layer(
                "ether", {"src": "52:00:00:00:00:00", "dst": "52:00:00:00:00:01"}
            )
            pkt.config_layer("ipv6", {"src": src_ip, "dst": dst_ip})
        pkt.config_layer("udp", {"dst": 0})
        pkt.config_layer("raw", {"payload": payload})
        pkt.send_pkt(crb=self.tester, tx_port=self.tx_interface, count=PACKET_COUNT)

        pkt_rec = self.tester.load_tcpdump_sniff_packets(inst)

        pcap_filename = "{0}.pcap".format(self.running_case)
        self.logger.info("Save pkts to {0}".format(packet.TMP_PATH + pcap_filename))
        pkt_rec.save_pcapfile(self.tester, pcap_filename)

        if len(pkt_rec) == 0:
            self.logger.error("IPsec forwarding failed")
            result = False
        for i in range(len(pkt_rec)):
            pkt_src_ip = pkt_rec.pktgen.strip_layer3("src", p_index=i)
            if pkt_src_ip != expected_src_ip:
                pkt_rec[i].show()
                self.logger.error(
                    "SRC IP does not match. Pkt:{0}, Expected:{1}".format(
                        pkt_src_ip, expected_src_ip
                    )
                )
                result = False
                break

            pkt_dst_ip = pkt_rec.pktgen.strip_layer3("dst", p_index=i)
            self.logger.debug(pkt_dst_ip)
            if pkt_dst_ip != expected_dst_ip:
                pkt_rec[i].show()
                self.logger.error(
                    "DST IP does not match. Pkt:{0}, Expected:{1}".format(
                        pkt_dst_ip, expected_dst_ip
                    )
                )
                result = False
                break

            packet_hex = pkt_rec[i]["ESP"].getfieldval("data")
            if packet_hex is None:
                self.logger.error("NO Payload !")
                result = False
                break
            payload_str = binascii.b2a_hex(packet_hex)
            self.logger.debug(payload_str)

            pkt_spi = hex(pkt_rec[i]["ESP"].getfieldval("spi"))
            self.logger.debug(pkt_spi)
            if pkt_spi != expected_spi:
                self.logger.error(
                    "SPI does not match. Pkt:{0}, Expected:{1}".format(
                        pkt_spi, expected_spi
                    )
                )
                result = False
                break

        self.verify(result, "FAILED")
