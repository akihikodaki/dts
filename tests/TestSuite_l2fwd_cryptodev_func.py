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
import hashlib
import hmac
import time

# Manually Install the CryptoMobile Python Library,
# Before running this test suite
# Web link : https://github.com/mitshell/CryptoMobile
import CryptoMobile.CM as cm
import pyDes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESCCM, AESGCM

import framework.utils as utils
import tests.cryptodev_common as cc
from framework.packet import Packet
from framework.test_case import TestCase


class TestL2fwdCrypto(TestCase):

    def set_up_all(self):
        self.core_config = "1S/3C/1T"
        self.number_of_ports = 2
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= self.number_of_ports,
                    "Not enough ports for " + self.nic)
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])

        self.logger.info("core config = " + self.core_config)
        self.logger.info("number of ports = " + str(self.number_of_ports))
        self.logger.info("dut ports = " + str(self.dut_ports))
        self.logger.info("ports_socket = " + str(self.ports_socket))

        self.core_list = self.dut.get_core_list(self.core_config, socket=self.ports_socket)
        self.core_mask = utils.create_mask(self.core_list)
        self.port_mask = utils.create_mask([self.dut_ports[0], self.dut_ports[1]])

        self.tx_port = self.tester.get_local_port(self.dut_ports[0])
        self.rx_port = self.tester.get_local_port(self.dut_ports[1])

        self.tx_interface = self.tester.get_interface(self.tx_port)
        self.rx_interface = self.tester.get_interface(self.rx_port)

        self.logger.info("core mask = " + self.core_mask)
        self.logger.info("port mask = " + self.port_mask)
        self.logger.info("tx interface = " + self.tx_interface)
        self.logger.info("rx interface = " + self.rx_interface)

        self._app_path = self.dut.apps_name['l2fwd-crypto']

        out = self.dut.build_dpdk_apps("./examples/l2fwd-crypto")
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")

        cc.bind_qat_device(self, self.drivername)

    def set_up(self):
        pass

    def test_qat_AES_XTS_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "qat_AES_XTS_00")

    def test_qat_AES_CBC_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "qat_AES_CBC_00")

    def test_qat_AES_CTR_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "qat_AES_CTR_00")

    def test_qat_AES_GCM_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "qat_AES_GCM_00")

    def test_qat_AES_CCM_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "qat_AES_CCM_00")

    def test_qat_h_MD_SHA_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "qat_h_MD_SHA_00")

    def test_qat_h_AES_XCBC_MAC_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "qat_h_AES_XCBC_MAC_01")

    def test_qat_3DES_CBC_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "qat_3DES_CBC_00")

    def test_qat_3DES_CTR_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "qat_3DES_CTR_00")

    def test_qat_AES_DOCSISBPI_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "qat_AES_DOCSISBPI_01")

    def test_qat_DES_DOCSISBPI_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "qat_DES_DOCSISBPI_01")

    def test_qat_SNOW3G_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "qat_snow3g_00")

    def test_qat_KASUMI_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "qat_kasumi_00")

    def test_qat_ZUC_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "qat_zuc_00")

    def test_qat_NULL_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "qat_NULL_auto")

    def test_aesni_mb_AES_CBC_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "aesni_mb_AES_CBC_00")

    def test_aesni_mb_AES_CTR_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "aesni_mb_AES_CTR_00")

    def test_aesni_mb_AES_DOCSISBPI_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "aesni_mb_AES_DOCSISBPI_01")

    def test_aesni_mb_AES_GCM_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "aesni_mb_aead_AES_GCM_00")

    def test_aesni_mb_AES_CCM_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "aesni_mb_AES_CCM_00")

    def test_aesni_gcm_AES_GCM_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "aesni_gcm_aead_AES_GCM_01")

    def test_aesni_mb_h_MD_SHA_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "aesni_mb_h_MD_SHA_00")

    def test_aesni_mb_3DES_CBC_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "aesni_mb_3DES_CBC_00")

    def test_kasumi_KASUMI_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "kasumi_kasumi_00")

    def test_null_NULL_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "null_NULL_auto")

    def test_snow3g_SNOW3G_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "snow3g_snow3g_00")

    def test_zuc_ZUC_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "zuc_zuc_00")

    def test_openssl_3DES_CBC_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "openssl_3DES_CBC_00")

    def test_openssl_3DES_CTR_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "openssl_3DES_CTR_00")

    def test_openssl_AES_CBC_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "openssl_AES_CBC_00")

    def test_openssl_AES_CTR_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "openssl_AES_CTR_00")

    def test_openssl_AES_GCM_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "openssl_AES_GCM_00")

    def test_openssl_AES_CCM_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "openssl_AES_CCM_00")

    def test_openssl_h_MD_SHA_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "openssl_h_MD_SHA_00")

    def test_openssl_DES_DOCSISBPI_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "openssl_DES_DOCSISBPI_01")

    def test_aesni_mb_DES_DOCSISBPI_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "aesni_mb_DES_DOCSISBPI_01")

    def test_aesni_mb_DES_CBC_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "aesni_mb_DES_CBC_00")

    def test_openssl_DES_CBC_auto(self):
        self.__execute_l2fwd_crypto_test(test_vectors, "openssl_DES_CBC_00")

    def test_scheduler_rr_AES_CBC_auto(self):
        vdev = '-a ' + ' -a '.join(cc.get_qat_devices(self, num=3))
        vdev += " --vdev crypto_scheduler0,slave=%s_qat_sym,slave=%s_qat_sym,slave=%s_qat_sym,\
                mode=round-robin" % tuple(cc.get_qat_devices(self, num=3))
        test_vectors["scheduler_AES_CBC_00"]['vdev'] = vdev
        test_vectors["scheduler_AES_CBC_00"]['mode'] = "rr"
        self.__execute_l2fwd_crypto_test(test_vectors, "scheduler_AES_CBC_00")

    def test_scheduler_rr_AES_GCM_auto(self):
        vdev = "-a 0000:00:00.0 --vdev crypto_aesni_mb1,name=aesni_mb_1"
        vdev += " --vdev crypto_aesni_mb2,name=aesni_mb_2"
        vdev += " --vdev crypto_aesni_mb3,name=aesni_mb_3"
        vdev += " --vdev crypto_scheduler0,slave=aesni_mb_1,slave=aesni_mb_2,slave=aesni_mb_3,mode=round-robin"
        test_vectors["scheduler_AES_GCM_00"]['vdev'] = vdev
        test_vectors["scheduler_AES_GCM_00"]['mode'] = "rr"
        self.__execute_l2fwd_crypto_test(test_vectors, "scheduler_AES_GCM_00")

    def test_scheduler_psb_AES_CBC_auto(self):
        vdev = '-a ' + ' -a '.join(cc.get_qat_devices(self, num=2))
        vdev += " --vdev crypto_scheduler0,slave=%s_qat_sym,slave=%s_qat_sym,\
                mode=packet-size-distr" % tuple(cc.get_qat_devices(self, num=2))
        test_vectors["scheduler_AES_CBC_00"]['vdev'] = vdev
        test_vectors["scheduler_AES_CBC_00"]['mode'] = "psb"
        self.__execute_l2fwd_crypto_test(test_vectors, "scheduler_AES_CBC_00")

    def test_scheduler_psb_AES_GCM_auto(self):
        vdev = '-a ' + ' -a '.join(cc.get_qat_devices(self, num=1))
        vdev += " --vdev crypto_aesni_mb1,name=aesni_mb_1"
        vdev += " --vdev crypto_scheduler0,slave=%s_qat_sym,slave=aesni_mb_1,\
                mode=packet-size-distr"% tuple(cc.get_qat_devices(self, num=1))
        test_vectors["scheduler_AES_GCM_00"]['vdev'] = vdev
        test_vectors["scheduler_AES_GCM_00"]['mode'] = "psb"
        self.__execute_l2fwd_crypto_test(test_vectors, "scheduler_AES_GCM_00")

    def test_scheduler_fo_AES_CBC_auto(self):
        vdev = '-a ' + ' -a '.join(cc.get_qat_devices(self, num=2))
        vdev += " --vdev crypto_scheduler0,slave=%s_qat_sym,slave=%s_qat_sym,\
                mode=fail-over" % tuple(cc.get_qat_devices(self, num=2))
        test_vectors["scheduler_AES_CBC_00"]['vdev'] = vdev
        test_vectors["scheduler_AES_CBC_00"]['mode'] = "fo"
        self.__execute_l2fwd_crypto_test(test_vectors, "scheduler_AES_CBC_00")

    def test_scheduler_fo_AES_GCM_auto(self):
        vdev = '-a ' + ' -a '.join(cc.get_qat_devices(self, num=1))
        vdev += " --vdev crypto_aesni_mb1,name=aesni_mb_1"
        vdev += " --vdev crypto_scheduler0,slave=%s_qat_sym,slave=aesni_mb_1,\
                mode=fail-over"% tuple(cc.get_qat_devices(self, num=1))
        test_vectors["scheduler_AES_GCM_00"]['vdev'] = vdev
        test_vectors["scheduler_AES_GCM_00"]['mode'] = "fo"
        self.__execute_l2fwd_crypto_test(test_vectors, "scheduler_AES_GCM_00")

    def test_scheduler_mm_AES_CBC_auto(self):
        vdev = '-a ' + ' -a '.join(cc.get_qat_devices(self, num=2))
        vdev += " --vdev crypto_scheduler0,slave=%s_qat_sym,slave=%s_qat_sym\
                mode=multi-core" % tuple(cc.get_qat_devices(self, num=2))
        test_vectors["scheduler_AES_CBC_00"]['vdev'] = vdev
        test_vectors["scheduler_AES_CBC_00"]['mode'] = "mm"
        self.__execute_l2fwd_crypto_test(test_vectors, "scheduler_AES_CBC_00")

    def test_scheduler_mm_AES_GCM_auto(self):
        vdev = '-a ' + ' -a '.join(cc.get_qat_devices(self, num=1))
        vdev += " --vdev crypto_aesni_mb1,name=aesni_mb_1"
        vdev += " --vdev crypto_scheduler0,slave=%s_qat_sym,slave=aesni_mb_1,\
                mode=multi-core"% tuple(cc.get_qat_devices(self, num=1))
        test_vectors["scheduler_AES_GCM_00"]['vdev'] = vdev
        test_vectors["scheduler_AES_GCM_00"]['mode'] = "mm"
        self.__execute_l2fwd_crypto_test(test_vectors, "scheduler_AES_GCM_00")

    def __calculate_total_cases_numb(self):
        alg_map = {}
        pmd_map = {}
        map_combine = {}
        count = 0
        alg = ""
        pmd = ""
        alg_list = ["AES_CBC", "AES_CTR", "AES_GCM", "3DES_CBC",
                    "3DES_CTR", "SNOW3G", "KASUMI", "ZUC", "NULL", "MD_SHA"]
        pmd_list = ["qat", "aesni_mb", "aesni_gcm", "snow3g",
                    "kasumi", "zuc", "openssl", "null"]
        valid_map = {
                    "qat": ["AES_CBC", "AES_CTR", "AES_GCM", "3DES_CBC",
                            "3DES_CTR", "SNOW3G", "KASUMI", "NULL", "MD_SHA"],
                    "aesni_mb": ["AES_CBC", "AES_CTR"],
                    "aesni_gcm": ["AES_GCM"],
                    "snow3g": ["SNOW3G"],
                    "kasumi": ["KASUMI"],
                    "zuc": ["ZUC"],
                    "openssl": ["AES_CBC", "AES_CTR", "AES_GCM", "3DES_CBC",
                                "3DES_CTR", "MD_SHA"],
                    "null": ["NULL"]
                    }

        for index, value in list(test_vectors.items()):
            test_vector_list = self.__test_vector_to_vector_list(value,
                core_mask="-1", port_mask=self.port_mask)
            count = count + len(test_vector_list)
            for i in alg_list:
                if (index.upper()).find(i) != -1:
                    alg = i
                    if i in alg_map:
                        alg_map[i] += len(test_vector_list)
                    else:
                        alg_map[i] = len(test_vector_list)
            for j in pmd_list:
                if (index).find(j) != -1:
                    pmd = j if j != "" else "qat"
                    if i in pmd_map:
                        pmd_map[j] += len(test_vector_list)
                    else:
                        pmd_map[j] = len(test_vector_list)
            if alg in valid_map[pmd]:
                temp_str = pmd + "_" + alg
                if temp_str in map_combine:
                    map_combine[temp_str] += len(test_vector_list)
                else:
                    map_combine[temp_str] = len(test_vector_list)
        for k, v in list(alg_map.items()):
            self.logger.info("Total {name} cases:\t\t\t{number}".format(name=k, number=v))
        for k, v in list(pmd_map.items()):
            self.logger.info("Total {name} cases:\t\t\t{number}".format(name=k, number=v))
        for k, v in list(map_combine.items()):
            self.logger.info("Total {name} cases:\t\t\t{number}".format(name=k, number=v))
        self.logger.info("Total cases:\t\t\t {0}".format(count))

    def __execute_l2fwd_crypto_test(self, test_vectors, test_vector_name):
        if cc.is_test_skip(self):
            return

        if test_vector_name not in test_vectors:
            self.logger.warning("SKIP : " + test_vector_name)
            return True

        test_vector = test_vectors[test_vector_name]

        test_vector_list = self.__test_vector_to_vector_list(test_vector,
                           core_mask=self.core_mask,
                           port_mask=self.port_mask)

        self.logger.info("Total Generated {0} Tests".format(len(test_vector_list)))

        running_case = self.running_case
        dut = self.dut.crb["IP"]
        dut_index = self._suite_result.internals.index(dut)
        target_index = self._suite_result.internals[dut_index+1].index(self.target)
        suite_index = self._suite_result.internals[dut_index+1][target_index+2].index(self.suite_name)
        if running_case in self._suite_result.internals[dut_index+1][target_index+2][suite_index+1]:
            case_index = self._suite_result.internals[dut_index+1][target_index+2][suite_index+1].index(running_case)
            self._suite_result.internals[dut_index+1][target_index+2][suite_index+1].pop(case_index+1)
            self._suite_result.internals[dut_index+1][target_index+2][suite_index+1].pop(case_index)

        for test_vector in test_vector_list:
            result = True
            self.logger.debug(test_vector)
            self.vector = []
            cmd_str = self.__test_vector_to_cmd(test_vector,
                                                core_mask=self.core_mask,
                                                port_mask=self.port_mask)
            self._suite_result.test_case = '_'.join(self.vector)
            self.dut.send_expect(cmd_str, "==", 40)
            time.sleep(5)

            payload = self.__format_hex_to_list(test_vector["input"])

            inst = self.tester.tcpdump_sniff_packets(self.rx_interface,
                    filters=[{'layer': 'ether',
                        'config': {'dst': '52:00:00:00:00:01'}}])

            PACKET_COUNT = 65
            pkt = Packet()
            pkt.assign_layers(["ether", "ipv4", "raw"])
            pkt.config_layer("ether", {"src": "52:00:00:00:00:00", "dst":"52:00:00:00:00:01"})
            pkt.config_layer("ipv4", {"src": "192.168.1.1", "dst": "192.168.1.2"})
            pkt.config_layer("raw", {"payload": payload})
            pkt.send_pkt(self.tester, tx_port=self.tx_interface, count=PACKET_COUNT)

            pkt_rec = self.tester.load_tcpdump_sniff_packets(inst)

            self.logger.info("Send pkgs: {}".format(PACKET_COUNT))
            self.logger.info("Receive pkgs: {}".format(len(pkt_rec)))
            self.verify(len(pkt_rec), "Can not receive any package")
            for i in range(len(pkt_rec)):
                packet_hex = pkt_rec[i]["Raw"].getfieldval("load")
                if packet_hex == None:
                    result = False
                    self.logger.info("no payload !")
                    continue
                cipher_text = str(binascii.b2a_hex(packet_hex), encoding='utf-8')
                if cipher_text.lower() == test_vector["output_cipher"].lower():

                    self.logger.debug(cipher_text)
                    self.logger.info("Cipher Matched.")
                else:
                    if test_vector["output_cipher"] != "":
                        result = False
                        self.logger.info("Cipher NOT Matched.")
                        self.logger.info("Cipher text in packet = " + str(cipher_text))
                        self.logger.info("Ref Cipher text       = " + test_vector["output_cipher"])
                    else:
                        self.logger.info("Skip Cipher, Since no cipher text set")

                hash_length = len(test_vector["output_hash"])//2
                if hash_length != 0:
                    if test_vector["auth_algo"] == "null":
                        hash_text = str(binascii.b2a_hex(pkt_rec.pktgen.pkt["Raw"].getfieldval("load")), encoding='utf-8')
                    else:
                        hash_text = str(binascii.b2a_hex(pkt_rec.pktgen.pkt["Padding"].getfieldval("load")), encoding='utf-8')
                    if hash_text.lower() == test_vector["output_hash"].lower():
                        self.logger.info("Hash Matched")
                    else:
                        result = False
                        self.logger.info("Hash NOT Matched")
                        self.logger.info("Hash text in packet = " + str(hash_text))
                        self.logger.info("Ref Hash text       = " + test_vector["output_hash"])
                else:
                    self.logger.info("Skip Hash, Since no hash text set")

            self.logger.info("Packet Size :    %d " % (len(test_vector["input"]) // 2))

            # Close l2fwd-crypto process
            self.dut.kill_all()

            if result:
                self._suite_result.test_case_passed()
            else:
                self._suite_result.test_case_failed("Test failed")

        self.verify(result, "Test Failed")

    def tear_down(self):
        self.dut.kill_all()

    def tear_down_all(self):
        pass

    def __test_vector_to_cmd(self, test_vector, core_mask="", port_mask=""):
        cores = ','.join(self.core_list)
        eal_opt_str = cc.get_eal_opt_str(self, {'l': cores}, add_port=True)

        EAL_SEP = " --"
        PORT_MASK = "" if port_mask == "" else " -p " + port_mask
        QUEUE_NUM = ""

        vdev = ""
        if test_vector["vdev"].find("scheduler") != -1:
            vdev = test_vector["vdev"]
            self.vector.append("Scheduler_" + test_vector["mode"])
        elif self.__check_field_in_vector(test_vector, "vdev"):
            vdev = "--vdev " + test_vector["vdev"] + "1" +\
                    " --vdev " + test_vector["vdev"] + "2" +\
                    " -a 0000:00:00.0"
            self.vector.append(test_vector["vdev"].upper())
        else:
            vdev = '-a ' + ' -a '.join(cc.get_qat_devices(self, num=2))
            self.vector.append("QAT")

        chain = ""
        if self.__check_field_in_vector(test_vector, "chain"):
            chain = " --chain " + test_vector["chain"]
            self.vector.append(test_vector["chain"].lower())

        cdev_type = ""
        if self.__check_field_in_vector(test_vector, "cdev_type"):
            cdev_type = " --cdev_type " + test_vector["cdev_type"]

        aad_random_size = ""
        cipher_algo = ""
        cipher_key = ""
        cipher_op = ""
        auth_algo = ""
        auth_key = ""
        auth_op = ""
        auth_key_random_size = ""
        aad = ""
        iv = ""
        digest_size = ""

        if test_vector["chain"].upper() == "AEAD":
            if self.__check_field_in_vector(test_vector, "cipher_algo"):
                cipher_algo = " --aead_algo " + test_vector["cipher_algo"]
                self.vector.append(test_vector["cipher_algo"])
            if self.__check_field_in_vector(test_vector, "cipher_op"):
                cipher_op = " --aead_op " + test_vector["cipher_op"]
                self.vector.append(test_vector["cipher_op"].lower())
            if self.__check_field_in_vector(test_vector, "cipher_key"):
                cipher_key = " --aead_key " + self.__format_hex_to_param(test_vector["cipher_key"])
                self.vector.append("aead_key_%d" % (len(test_vector["cipher_key"])//2))
            if self.__check_field_in_vector(test_vector, "iv"):
                iv = " --aead_iv " + self.__format_hex_to_param(test_vector["iv"])
                self.vector.append('iv_%d' % (len(test_vector["iv"])//2))
            if self.__check_field_in_vector(test_vector, "aad"):
                aad = " --aad " + self.__format_hex_to_param(test_vector["aad"])
                self.vector.append('aad_%d' % (len(test_vector["aad"])//2))
            if self.__check_field_in_vector(test_vector, "digest_size"):
                digest_size = " --digest " + str(test_vector["digest_size"])
                self.vector.append('digest_%d' % test_vector["digest_size"])
        else:
            if self.__check_field_in_vector(test_vector, "cipher_algo"):
                cipher_algo = " --cipher_algo " + test_vector["cipher_algo"]
                self.vector.append(test_vector["cipher_algo"])
            if self.__check_field_in_vector(test_vector, "cipher_op"):
                cipher_op = " --cipher_op " + test_vector["cipher_op"]
                self.vector.append(test_vector["cipher_op"].lower())

            if self.__check_field_in_vector(test_vector, "cipher_key"):
                cipher_key = " --cipher_key " + self.__format_hex_to_param(test_vector["cipher_key"])
                self.vector.append('cipher_key_%d' % (len(test_vector["cipher_key"])//2))
            if self.__check_field_in_vector(test_vector, "iv"):
                iv = " --cipher_iv " + self.__format_hex_to_param(test_vector["iv"])
                self.vector.append('cipher_iv_%d' % (len(test_vector["iv"])//2))

            if self.__check_field_in_vector(test_vector, "auth_algo"):
                auth_algo = " --auth_algo " + test_vector["auth_algo"]
                self.vector.append(test_vector["auth_algo"])

            if self.__check_field_in_vector(test_vector, "auth_op"):
                auth_op = " --auth_op " + test_vector["auth_op"]
                self.vector.append(test_vector["auth_op"].lower())

            if self.__check_field_in_vector(test_vector, "auth_key"):
                auth_key = " --auth_key " + self.__format_hex_to_param(test_vector["auth_key"])
                self.vector.append('auth_key_%d' % (len(test_vector["auth_key"])//2))

            if self.__check_field_in_vector(test_vector, "auth_key_random_size"):
                auth_key_random_size = " --auth_key_random_size " + test_vector["auth_key_random_size"]
                self.vector.append('auth_key_random_size_%d' % len(test_vector["auth_key_random_size"]))

            if self.__check_field_in_vector(test_vector, "aad"):
                aad = " --auth_iv " + self.__format_hex_to_param(test_vector["aad"])
                self.vector.append('auth_iv_%d' % (len(test_vector["aad"])//2))

            if self.__check_field_in_vector(test_vector, "aad_random_size"):
                aad_random_size = " --aad_random_size " + test_vector["aad_random_size"]
                self.vector.append('aad_random_size_%d' % len(test_vector["aad_random_size"]))

            if self.__check_field_in_vector(test_vector, "digest_size"):
                digest_size = " --digest " + str(test_vector["digest_size"])
                self.vector.append('digest_%d' % test_vector["digest_size"])

        cmd_str = " ".join([self._app_path, eal_opt_str, vdev, EAL_SEP, PORT_MASK,
                            QUEUE_NUM, chain, cdev_type, cipher_algo,
                            cipher_op, cipher_key, iv, auth_algo, auth_op,
                            auth_key, auth_key_random_size, aad,
                            aad_random_size, digest_size, "--no-mac-updating"])
        return cmd_str

    def __check_field_in_vector(self, test_vector, field_name):
        if field_name in test_vector and test_vector[field_name]:
            return True
        return False

    def __format_hex_to_param(self, hex_str, sep=":", prefix=""):
        if not hex_str:
            return ""
        if len(hex_str) == 1:
            return prefix + "0" + hex_str

        result = prefix + hex_str[0:2]
        for i in range(2, len(hex_str), 2):
            if len(hex_str) < i + 2:
                result = result + sep + "0" + hex_str[i:]
            else:
                result = result + sep + hex_str[i:i+2]

        return result

    def __format_hex_to_list(self, hex_str):
        if not hex_str:
            return []
        if len(hex_str) == 1:
            return [hex_str]

        result = []
        result.append(hex_str[0:2])
        for i in range(2, len(hex_str), 2):
            if len(hex_str) < i + 2:
                result.append(hex_str[i:])
            else:
                result.append(hex_str[i:i+2])
        return result

    def __gen_input(self, length, pattern=None):
        pattern = "11"
        input_str = ""
        for i in range(length):
            input_str += pattern
        return input_str

    def __gen_key(self, length, pattern=None, mask="000000"):
        base_key = "000102030405060708090a0b0c0d0e0f"
        key = ""
        n = length // 16
        for i in range(n):
            key = key + base_key
            base_key = base_key[2:] + base_key[0:2]
        m = length % 16
        key = key + base_key[0:2*m]
        return key

    def __cipher_algorithm_for_cryptography_block_size_check(self, algo):
        block_size = 8
        algo_block_map = {
                          "aes-cbc": 16,
                          "aes-ctr": 16,
                          "aes-gcm": 16,
                          "3des-cbc": 8,
                          "3des-ctr": 8,
                          "des-cbc": 8
                          }
        if algo in algo_block_map:
            block_size = algo_block_map[algo]

        return block_size

    def __cryptography_cipher(self, vector):
        key = binascii.a2b_hex(vector["cipher_key"])
        iv = binascii.a2b_hex(vector["iv"])

        cipher_str = ""
        if vector["chain"].upper() != "AEAD":
            if vector["cipher_algo"] == "aes-cbc":
                cipher_algo = algorithms.AES(key)
                cipher_mode = modes.CBC(iv)
            elif vector["cipher_algo"] == "aes-ctr":
                cipher_algo = algorithms.AES(key)
                cipher_mode = modes.CTR(iv)
            elif vector["cipher_algo"] == "3des-cbc":
                cipher_algo = algorithms.TripleDES(key)
                cipher_mode = modes.CBC(iv)
            elif vector["cipher_algo"] == "3des-ctr":
                cipher_algo = algorithms.TripleDES(key)
                cipher_mode = modes.CTR(iv)
            elif vector["cipher_algo"] == "aes-xts":
                cipher_algo = algorithms.AES(key)
                cipher_mode = modes.XTS(iv)
            elif vector["cipher_algo"] == "des-cbc":
                cipher = pyDes.des(key, pyDes.CBC, iv)
                if vector["cipher_op"] == "DECRYPT":
                    cipher_str = cipher.decrypt(binascii.a2b_hex(vector["input"]))
                else:
                    cipher_str = cipher.encrypt(binascii.a2b_hex(vector["input"]))
            else:
                cipher_algo = algorithms.AES(key)
                cipher_mode = modes.CBC(iv)

            # this is workaround, need to refact to calculate method by diff lib
            if cipher_str == "":
                cipher = Cipher(cipher_algo, cipher_mode, backend=default_backend())
                if vector["cipher_op"] == "DECRYPT":
                    encryptor = cipher.decryptor()
                else:
                    encryptor = cipher.encryptor()
                cipher_str = encryptor.update(binascii.a2b_hex(vector["input"])) + encryptor.finalize()
        else:
            if vector["cipher_algo"] == "aes-gcm":
                aesgcm = AESGCM(key)
                cipher_str = aesgcm.encrypt(iv,
                                            binascii.a2b_hex(vector["input"]),
                                            binascii.a2b_hex(vector["aad"]))
                cipher_str = cipher_str[0:-16]
            elif vector["cipher_algo"] == "aes-ccm":
                aesccm = AESCCM(key)
                cipher_str = aesccm.encrypt(iv,
                                            binascii.a2b_hex(vector["input"]),
                                            binascii.a2b_hex(vector["aad"]))
                cipher_str = cipher_str[0:-16]

        return binascii.b2a_hex(cipher_str)

    def __CryptoMoble_cipher(self, vector):
        cipher_str = ""
        out_str = ""
        cipher_algo = vector['cipher_algo']

        mBitlen = 8 * (len(vector['input']) // 2)
        bin_input = bytearray.fromhex(vector["input"])
        str_input = str(bin_input, encoding='utf-8')
        bin_key = binascii.a2b_hex(vector["cipher_key"])
        bin_key = str(bin_key, encoding='utf-8')

        if ((cipher_algo.upper()).find("KASUMI") != -1):
            vector["iv"] = vector["iv"][:10] + "000000"
            out_str = cm.UEA1(key=bin_key, count=66051, bearer=0,
                           dir=1, data=str_input, bitlen=mBitlen)

        elif ((cipher_algo.upper()).find("SNOW3G") != -1):
            vector["iv"] = "00000000000000000000000000000000"
            out_str = cm.UEA2(key=bin_key, count=0, bearer=0, dir=0,
                           data=str_input, bitlen=mBitlen)
        elif ((cipher_algo.upper()).find("ZUC") != -1):
            vector["iv"] = "00010203040000000001020304000000"
            out_str = cm.EEA3(key=bin_key, count=0x10203, bearer=0, dir=1,
                           data=str_input, bitlen=mBitlen)

        cipher_str = out_str.upper()

        return cipher_str

    def __gen_null_cipher_out(self, vector):
        cipher_str = ""
        if (vector['chain'] == "CIPHER_ONLY") or (vector['chain'] == "CIPHER_HASH"):
            cipher_str = vector['input']
        elif (vector['chain'] == "HASH_CIPHER"):
            cipher_str = vector['output_hash']
        return cipher_str

    def __gen_cipher_output(self, vector):
        if vector["chain"] == "HASH_ONLY":
            vector["output_cipher"] = ""
            return

        if vector["output_cipher"] != "*":
            return

        cipher_str = ""

        if(((vector['cipher_algo']).upper()).find("KASUMI") != -1) or  \
                (((vector['cipher_algo']).upper()).find("SNOW3G") != -1) or \
                (((vector['cipher_algo']).upper()).find("ZUC") != -1):
            cipher_str = self.__CryptoMoble_cipher(vector)
        elif (vector['cipher_algo'] == "NULL"):
            cipher_str = self.__gen_null_cipher_out(vector)
        elif ((vector['cipher_algo']).upper()).find("DOCSISBPI") != -1:
            cipher_str = len(vector["input"]) * "a"
        elif (vector['cipher_algo']).upper() == "NULL":
            cipher_str = vector["input"] if vector["chain"].upper().find("HASH_") == -1 else vector["output_hash"]
        else:
            cipher_str = str(self.__cryptography_cipher(vector), encoding='utf-8')
        vector["output_cipher"] = cipher_str.lower()

    def __gen_kasumi_hash(self, vector):
        auth_str = ""
        auth_algo = vector['auth_algo']
        mBitlen = 8 * (len(vector['input']) / 2)
        bin_input = bytearray.fromhex(vector["input"])
        str_input = str(bin_input, encoding='utf-8')
        bin_key = binascii.a2b_hex(vector["auth_key"])
        bin_key = str(bin_key, encoding='utf-8')

        hash_out = cm.UIA1(key=bin_key, count=0X10203, fresh=0X4050607, dir=0,
                        data=str_input)
        auth_str = hash_out.lower()

        vector["input"] = '0001020304050607' + vector["input"] + '40'
        return auth_str

    def __gen_snow3g_hash(self, vector):
        auth_str = ""
        auth_algo = vector['auth_algo']
        mBitlen = 8 * (len(vector['input']) / 2)
        bin_input = bytearray.fromhex(vector["input"])
        str_input = str(bin_input, encoding='utf-8')
        bin_key = binascii.a2b_hex(vector["auth_key"])
        bin_key = str(bin_key, encoding='utf-8')
        vector["aad"] = "00000000000000000000000000000000"

        hash_out = cm.UIA2(key=bin_key, count=0, fresh=0, dir=0,
                        data=str_input)

        auth_str = hash_out.lower()

        return auth_str

    def __gen_zuc_hash(self, vector):
        auth_str = ""
        auth_algo = vector['auth_algo']
        mBitlen = 8 * (len(vector['input']) / 2)
        bin_input = bytearray.fromhex(vector["input"])
        str_input = str(bin_input, encoding='utf-8')
        bin_key = binascii.a2b_hex(vector["auth_key"])
        bin_key = str(bin_key, encoding='utf-8')

        vector["aad"] = "00000000000000000000000000000000"

        hash_out = cm.EIA3(key=bin_key, count=0, bearer=0, dir=0, data=str_input, bitlen=mBitlen)
        auth_str = hash_out.lower()

        return auth_str

    def __gen_null_hash(self, vector):
        auth_str = ""
        if (vector['chain'] == "HASH_ONLY") or (vector['chain'] == "HASH_CIPHER"):
            auth_str = vector['input']
        elif (vector['chain'] == "CIPHER_HASH"):
            auth_str = vector['output_cipher']
        return auth_str

    def __gen_hash_output(self, vector):
        if vector["chain"] == "CIPHER_ONLY":
            vector["output_hash"] == ""
            return

        if vector["output_hash"] != "*":
            return

        if vector["chain"] == "HASH_ONLY":
            vector["output_cipher"] = ""

        hash_str = ""

        if vector["chain"] == "CIPHER_HASH":
            input_str = vector["output_cipher"]
        else:
            input_str = vector["input"]

        auth_algo = vector["auth_algo"]
        if auth_algo == "md5-hmac":
            hash_str = hmac.new(binascii.a2b_hex(vector["auth_key"]),
                    binascii.a2b_hex(input_str), hashlib.md5).hexdigest()
        elif auth_algo == "sha1-hmac":
            hash_str = hmac.new(binascii.a2b_hex(vector["auth_key"]),
                    binascii.a2b_hex(input_str), hashlib.sha1).hexdigest()
        elif auth_algo == "sha2-224-hmac":
            hash_str = hmac.new(binascii.a2b_hex(vector["auth_key"]),
                    binascii.a2b_hex(input_str), hashlib.sha224).hexdigest()
        elif auth_algo == "sha2-256-hmac":
            hash_str = hmac.new(binascii.a2b_hex(vector["auth_key"]),
                    binascii.a2b_hex(input_str), hashlib.sha256).hexdigest()
        elif auth_algo == "sha2-384-hmac":
            hash_str = hmac.new(binascii.a2b_hex(vector["auth_key"]),
                    binascii.a2b_hex(input_str), hashlib.sha384).hexdigest()
        elif auth_algo == "sha2-512-hmac":
            hash_str = hmac.new(binascii.a2b_hex(vector["auth_key"]),
                    binascii.a2b_hex(input_str), hashlib.sha512).hexdigest()
        elif auth_algo == "aes-xcbc-mac":
            pass
        elif auth_algo == "aes-gcm":
            key = binascii.a2b_hex(vector["cipher_key"])
            iv = binascii.a2b_hex(vector["iv"])
            aesgcm = AESGCM(key)

            hash_str = aesgcm.encrypt(iv,
                                      binascii.a2b_hex(vector["input"]),
                                      binascii.a2b_hex(vector["aad"]))
            hash_str = hash_str[-16:]
            hash_str = binascii.b2a_hex(hash_str)
        elif auth_algo == "aes-ccm":
            key = binascii.a2b_hex(vector["cipher_key"])
            iv = binascii.a2b_hex(vector["iv"])
            aesccm = AESCCM(key)
            hash_str = aesccm.encrypt(iv,
                                      binascii.a2b_hex(vector["input"]),
                                      binascii.a2b_hex(vector["aad"]))
            hash_str = hash_str[-16:]
            hash_str = binascii.b2a_hex(hash_str)
        elif auth_algo == "aes-gmac":
            pass
        elif auth_algo == "snow3g-uia2":
            hash_str = self.__gen_snow3g_hash(vector)
        elif auth_algo == "zuc-eia3":
            hash_str = self.__gen_zuc_hash(vector)
        elif auth_algo == "kasumi-f9":
            hash_str = self.__gen_kasumi_hash(vector)
        elif auth_algo == "null":
            hash_str = self.__gen_null_hash(vector)
        elif auth_algo == "md5":
             hash_str = hashlib.md5(binascii.a2b_hex(vector["auth_key"])).hexdigest()
        elif auth_algo == "sha1":
            hash_str = hashlib.sha1(binascii.a2b_hex(vector["auth_key"])).hexdigest()
        elif auth_algo == "sha2-224":
            hash_str = hashlib.sha224(binascii.a2b_hex(vector["auth_key"])).hexdigest()
        elif auth_algo == "sha2-256":
            hash_str = hashlib.sha256(binascii.a2b_hex(vector["auth_key"])).hexdigest()
        elif auth_algo == "sha2-384":
            hash_str = hashlib.sha384(binascii.a2b_hex(vector["auth_key"])).hexdigest()
        elif auth_algo == "sha2-512":
            hash_str = hashlib.sha512(binascii.a2b_hex(vector["auth_key"])).hexdigest()
        else:
            pass
        if not isinstance(hash_str, str):
            hash_str = str(hash_str, encoding='utf-8')
        vector["output_hash"] = hash_str.lower()
        self.__actually_pmd_hash(vector)

    def __gen_output(self, vector, cmds, core_mask="", port_mask=""):
        if core_mask != "-1":
            self.__gen_cipher_output(vector)
            self.__gen_hash_output(vector)
        cmds.append(vector)

    def __var2list(self, var):
        var_list = var if isinstance(var, list) else [var]
        return var_list

    def __is_valid_op(self, chain, op):
        chain_op_map = {
                "AEAD": ["ENCRYPT", "GENERATE"],
                "CIPHER_ONLY": ["ENCRYPT", "DECRYPT"],
                "HASH_ONLY": ["GENERATE", "VERIFY"],
                "CIPHER_HASH": ["ENCRYPT", "GENERATE"],
                "HASH_CIPHER": ["DECRYPT", "VERIFY"],
                }
        if op in chain_op_map[chain]:
            return True
        return False

    def __is_valid_size(self, key_type, algo, size):
        algo_size_map = {
                "aes-xts": {
                    "cipher_key": [32, 64],
                    "iv": [16],
                    },
                "aes-cbc": {
                    "cipher_key": [16, 24, 32],
                    "iv": [16],
                    },
                "aes-ctr": {
                    "cipher_key": [16, 24, 32],
                    "iv": [12, 16]
                    },
                "3des-cbc": {
                    "cipher_key": [8, 16, 24],
                    "iv": [8]
                    },
                "3des-ctr": {
                    "cipher_key": [16, 24],
                    "iv": [8]
                    },
                "aes-gcm": {
                    "cipher_key": [16, 24, 32],
                    "aad": [0, 1, 2, 3, 4, 5, 6, 8, 9, 12, 16, 24, 32, 64, 128, 155, 256, 1024, 65535],
                    "iv": [12],
                    "digest_size": [8,12,16]
                    },
                "aes-ccm": {
                    "cipher_key": [16, 24, 32],
                    "aad": [0, 1, 2, 3, 4, 5, 6, 8, 9, 12, 16, 24, 32, 64, 128, 155, 256, 1024, 65535],
                    "iv": [7, 8, 9, 10, 11, 12, 13],
                    "digest_size": [4, 6, 8, 10, 12, 14, 16]
                },
                "aes-docsisbpi": {
                    "cipher_key": [16, 32],
                    "iv": [16],
                    },
                "des-docsisbpi": {
                    "cipher_key": [8],
                    "iv": [8],
                    },
                "des-cbc": {
                    "cipher_key": [8],
                    "iv": [8],
                    },
                "snow3g-uea2": {
                    "cipher_key": [16],
                    "iv": [16]
                    },
                "kasumi-f8": {
                    "cipher_key": [16],
                    "iv": [8]
                    },
                "zuc-eea3": {
                    "cipher_key": [16],
                    "iv": [16]
                    },
                "null": {
                    "cipher_key": [0],
                    "auth_key": [0],
                    "aad": [0],
                    "iv": [0]
                    },
                "md5-hmac": {
                    "auth_key": [64],
                    "aad": [0],
                    "digest_size": [12, 16]
                    },
                "sha1-hmac": {
                    "auth_key": [64],
                    "aad": [0],
                    "digest_size": [12, 20]
                    },
                "sha2-224-hmac": {
                    "auth_key": [64],
                    "aad": [0],
                    "digest_size": [14, 28]
                    },
                "sha2-256-hmac": {
                    "auth_key": [64],
                    "aad": [0],
                    "digest_size": [16, 32]
                    },
                "sha2-384-hmac": {
                    "auth_key": [128],
                    "aad": [0],
                    "digest_size": [24, 48]
                    },
                "sha2-512-hmac": {
                    "auth_key": [128],
                    "aad": [0],
                    "digest_size": [32, 64]
                    },
                "aes-xcbc-mac": {
                    "auth_key": [16],
                    "aad": [0],
                    "digest_size": [12, 16]
                    },
                "aes-gmac": {
                    "auth_key": [16, 24, 32],
                    "aad": [1, 12, 16, 64, 128, 256, 65535],
                    "digest_size": [8, 12, 16]
                    },
                "snow3g-uia2": {
                    "auth_key": [16],
                    "aad": [16],
                    "digest_size": [4]
                    },
                "kasumi-f9": {
                    "auth_key": [16],
                    "aad": [8],
                    "digest_size": [4]
                    },
                "zuc-eia3": {
                    "auth_key": [16],
                    "aad": [16],
                    "digest_size": [4]
                    },
                "md5": {
                    "auth_key": [0],
                    "aad": [0],
                    "digest_size": [16]
                    },
                "sha1": {
                    "auth_key": [0],
                    "aad": [0],
                    "digest_size": [20]
                    },
                "sha2-224": {
                    "auth_key": [0],
                    "aad": [0],
                    "digest_size": [28]
                    },
                "sha2-256": {
                    "auth_key": [0],
                    "aad": [0],
                    "digest_size": [32]
                    },
                "sha2-384": {
                    "auth_key": [0],
                    "aad": [0],
                    "digest_size": [48]
                    },
                "sha2-512": {
                    "auth_key": [0],
                    "aad": [0],
                    "digest_size": [64]
                    },
                }
        result = False
        if algo in algo_size_map:
            if key_type in algo_size_map[algo]:
                if size in algo_size_map[algo][key_type]:
                    result = True
        return result

    def __actually_pmd_hash(self, vector):
        auth_algo_dgst_map = [
                "md5-hmac",
                "sha1-hmac",
                "sha2-224-hmac",
                "sha2-256-hmac",
                "sha2-384-hmac",
                "sha2-512-hmac",
                "aes-xcbc-mac"
                ]
        if vector["auth_algo"] in auth_algo_dgst_map:
            digest = vector["digest_size"]
            if digest >= (len(vector["output_hash"]) // 2):
                vector["output_hash"] = vector["output_hash"]
            else:
                vector["output_hash"] = (vector["output_hash"])[0:2*digest]

    def __iter_cipher_algo(self, vector, vector_list, core_mask="", port_mask=""):
        test_vector = vector.copy()
        if test_vector["chain"] == "HASH_ONLY":
            test_vector["cipher_algo"] = ""
            self.__iter_cipher_op(test_vector, vector_list, core_mask, port_mask)
        else:
            cipher_algo_list = self.__var2list(test_vector["cipher_algo"])
            for cipher_algo in cipher_algo_list:
                test_vector = vector.copy()
                test_vector["cipher_algo"] = cipher_algo
                self.__iter_cipher_op(test_vector, vector_list, core_mask, port_mask)

    def __iter_cipher_op(self, vector, vector_list, core_mask="", port_mask=""):
        test_vector = vector.copy()
        if test_vector["chain"] == "HASH_ONLY":
            test_vector["cipher_op"] = ""
            self.__iter_cipher_key(test_vector, vector_list, core_mask, port_mask)
        else:
            cipher_op_list = self.__var2list(test_vector["cipher_op"])
            for cipher_op in cipher_op_list:
                if self.__is_valid_op(test_vector["chain"], cipher_op):
                    test_vector = vector.copy()
                    test_vector["cipher_op"] = cipher_op
                    self.__iter_cipher_key(test_vector, vector_list,
                            core_mask, port_mask)

    def __iter_cipher_key(self, vector, vector_list, core_mask="", port_mask=""):
        test_vector = vector.copy()
        if test_vector["chain"] == "HASH_ONLY":
            test_vector["cipher_key"] = ""
            self.__iter_iv(test_vector, vector_list, core_mask, port_mask)
        else:
            cipher_key_list = self.__var2list(test_vector["cipher_key"])
            for cipher_key in cipher_key_list:
                test_vector = vector.copy()
                if isinstance(cipher_key, int):
                    if self.__is_valid_size("cipher_key",
                            test_vector["cipher_algo"],
                            cipher_key):
                        test_vector["cipher_key"] = self.__gen_key(cipher_key)
                        self.__iter_iv(test_vector, vector_list, core_mask, port_mask)
                    else:
                        continue
                else:
                    test_vector["cipher_key"] = cipher_key
                    self.__iter_iv(test_vector, vector_list, core_mask, port_mask)

    def __iter_iv(self, vector, vector_list, core_mask="", port_mask=""):
        test_vector = vector.copy()
        if test_vector["chain"] == "HASH_ONLY":
            test_vector["iv"] = ""
            self.__iter_auth_algo(test_vector, vector_list, core_mask, port_mask)
        else:
            iv_list = self.__var2list(test_vector["iv"])
            for iv in iv_list:
                test_vector = vector.copy()
                if isinstance(iv, int):
                    if self.__is_valid_size("iv",
                            test_vector["cipher_algo"],
                            iv):
                        test_vector["iv"] = self.__gen_key(iv)
                        self.__iter_auth_algo(test_vector, vector_list,
                                core_mask, port_mask)
                    else:
                        continue
                else:
                    test_vector["iv"] = iv
                    self.__iter_auth_algo(test_vector, vector_list,
                            core_mask, port_mask)

    def __iter_auth_algo(self, vector, vector_list, core_mask="", port_mask=""):
        test_vector = vector.copy()
        if test_vector["chain"] in ["CIPHER_ONLY", "AEAD"]:
            test_vector["auth_algo"] = ""
            self.__iter_auth_op(test_vector, vector_list, core_mask, port_mask)
        else:
            auth_algo_list = self.__var2list(test_vector["auth_algo"])
            for auth_algo in auth_algo_list:
                test_vector = vector.copy()
                test_vector["auth_algo"] = auth_algo
                self.__iter_auth_op(test_vector, vector_list, core_mask, port_mask)

    def __iter_auth_op(self, vector, vector_list, core_mask="", port_mask=""):
        test_vector = vector.copy()
        if test_vector["chain"] in ["CIPHER_ONLY", "AEAD"]:
            test_vector["auth_op"] = ""
            self.__iter_auth_key(test_vector, vector_list, core_mask, port_mask)
        else:
            auth_op_list = self.__var2list(test_vector["auth_op"])
            for auth_op in auth_op_list:
                if self.__is_valid_op(test_vector["chain"], auth_op):
                    test_vector = vector.copy()
                    test_vector["auth_op"] = auth_op
                    self.__iter_auth_key(test_vector, vector_list,
                            core_mask, port_mask)

    def __iter_auth_key(self, vector, vector_list, core_mask="", port_mask=""):
        test_vector = vector.copy()
        if test_vector["chain"] in ["CIPHER_ONLY", "AEAD"]:
            test_vector["auth_key"] = ""
            self.__iter_aad(test_vector, vector_list, core_mask, port_mask)
        else:
            auth_key_list = self.__var2list(test_vector["auth_key"])
            for auth_key in auth_key_list:
                test_vector = vector.copy()
                if isinstance(auth_key, int):
                    if self.__is_valid_size("auth_key",
                            test_vector["auth_algo"],
                            auth_key):
                        test_vector["auth_key"] = self.__gen_key(auth_key)
                        self.__iter_aad(test_vector, vector_list, core_mask, port_mask)
                    else:
                        continue
                else:
                    test_vector["auth_key"] = auth_key
                    self.__iter_aad(test_vector, vector_list, core_mask, port_mask)

    def __iter_aad(self, vector, vector_list, core_mask="", port_mask=""):
        test_vector = vector.copy()
        if test_vector["chain"] == "CIPHER_ONLY":
            test_vector["aad"] = ""
            self.__digest_size(test_vector, vector_list, core_mask, port_mask)
        else:
            aad_list = self.__var2list(test_vector["aad"])
            for aad in aad_list:
                test_vector = vector.copy()
                if isinstance(aad, int):
                    if self.__is_valid_size("aad", test_vector["auth_algo"], aad) or\
                            (test_vector["chain"] == "AEAD" and\
                            self.__is_valid_size("aad", test_vector["cipher_algo"],
                            aad)):
                        test_vector["aad"] = self.__gen_key(aad)
                        self.__digest_size(test_vector, vector_list,
                                core_mask, port_mask)
                    else:
                        continue
                else:
                    test_vector["aad"] = aad
                    self.__digest_size(test_vector, vector_list,
                            core_mask, port_mask)

    def __digest_size(self, vector, vector_list, core_mask = "", port_mask = ""):
        test_vector = vector.copy()
        if test_vector["chain"] == "CIPHER_ONLY":
            test_vector["digest_size"] = ""
            self.__iter_input(test_vector, vector_list, core_mask, port_mask)
        else:
            digest_list = self.__var2list(test_vector["digest_size"])
            for digest in digest_list:
                test_vector = vector.copy()
                if isinstance(digest, int):
                    if self.__is_valid_size("digest_size", test_vector["auth_algo"], digest)\
                            or (test_vector["chain"] == "AEAD" and\
                            self.__is_valid_size("digest_size", test_vector["cipher_algo"],
                            digest)):
                        test_vector["digest_size"] = digest
                        self.__iter_input(test_vector, vector_list,
                                          core_mask, port_mask)
                    else:
                        continue
                else:
                    test_vector["digest_size"] = digest
                    self.__iter_input(test_vector, vector_list,
                                    core_mask, port_mask)

    def __iter_input(self, vector, vector_list, core_mask="", port_mask=""):
        input_list = self.__var2list(vector["input"])
        for input_data in input_list:
            test_vector = vector.copy()
            if isinstance(input_data, int):
                test_vector["input"] = self.__gen_input(input_data)
            else:
                test_vector["input"] = input_data

            self.__gen_output(test_vector, vector_list, core_mask, port_mask)

    def __test_vector_to_vector_list(self, test_vector, core_mask="", port_mask=""):
        vector_list = []

        chain_list = self.__var2list(test_vector["chain"])

        for chain in chain_list:
            test_vector["chain"] = chain
            self.__iter_cipher_algo(test_vector, vector_list, core_mask, port_mask)
        return vector_list


test_vectors = {
    "qat_AES_CBC_00": {
        "vdev": "",
        "chain": ["CIPHER_ONLY", "CIPHER_HASH"],
        "cdev_type": "HW",
        "cipher_algo": ["aes-cbc"],
        "cipher_op": ["ENCRYPT", "DECRYPT"],
        "cipher_key": [16, 24, 32],
        "iv": [16],
        "auth_algo": ["sha1-hmac", "sha2-224-hmac", "sha2-256-hmac",
                      "sha2-384-hmac", "sha2-512-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [20, 28, 32, 48],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "qat_AES_CTR_00": {
        "vdev": "",
        "chain": ["CIPHER_ONLY", "CIPHER_HASH"],
        "cdev_type": "HW",
        "cipher_algo": ["aes-ctr"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16],
        "iv": [16],
        "auth_algo": ["sha1-hmac", "sha2-224-hmac", "sha2-256-hmac",
                      "sha2-384-hmac", "sha2-512-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [20, 28, 32, 48],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "qat_AES_GCM_00": {
        "vdev": "",
        "chain": ["AEAD"],
        "cdev_type": "HW",
        "cipher_algo": ["aes-gcm"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16, 24, 32],
        "iv": [12],
        "auth_algo": ["aes-gcm"],
        "auth_op": ["GENERATE"],
        "auth_key": [16],
        "auth_key_random_size": "",
        "aad": [16],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [8, 16],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "qat_AES_CCM_00": {
        "vdev": "",
        "chain": ["AEAD"],
        "cdev_type": "HW",
        "cipher_algo": ["aes-ccm"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16],
        "iv": [7, 8, 9, 10, 11, 12, 13],
        "auth_algo": ["aes-ccm"],
        "auth_op": ["GENERATE"],
        "auth_key": [16],
        "auth_key_random_size": "",
        "aad": [8],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [8, 16],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "qat_h_MD_SHA_00": {
        "vdev": "",
        "chain": ["HASH_ONLY"],
        "cdev_type": "HW",
        "cipher_algo": "",
        "cipher_op": "",
        "cipher_key": "",
        "iv": "",
        "auth_algo":  ["md5-hmac", "sha1-hmac", "sha2-224-hmac", "sha2-256-hmac",
                      "sha2-384-hmac", "sha2-512-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [12, 16, 20, 28, 48, 64],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "qat_h_AES_XCBC_MAC_01": {
        "vdev": "",
        "chain": "HASH_ONLY",
        "cdev_type": "HW",
        "cipher_algo": "",
        "cipher_op": "",
        "cipher_key": "",
        "iv": "",
        "auth_algo": ["aes-xcbc-mac"],
        "auth_op": "GENERATE",
        "auth_key": [16],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [12],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "qat_DES_CBC_00": {
        "vdev": "",
        "chain": ["CIPHER_ONLY", "CIPHER_HASH"],
        "cdev_type": "HW",
        "cipher_algo": ["des-cbc"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [8],
        "iv": [8],
        "auth_algo": ["sha1-hmac", "sha2-224-hmac", "sha2-256-hmac",
                      "sha2-384-hmac", "sha2-512-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [20, 28, 32, 48],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "qat_3DES_CBC_00": {
        "vdev": "",
        "chain": ["CIPHER_ONLY", "CIPHER_HASH"],
        "cdev_type": "HW",
        "cipher_algo": ["3des-cbc"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [8, 16, 24],
        "iv": [8],
        "auth_algo": ["sha1-hmac", "sha2-224-hmac", "sha2-256-hmac",
                      "sha2-384-hmac", "sha2-512-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [20, 28, 32, 48],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "qat_3DES_CTR_00": {
        "vdev": "",
        "chain": ["CIPHER_ONLY", "CIPHER_HASH"],
        "cdev_type": "HW",
        "cipher_algo": ["3des-ctr"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [24],
        "iv": [8],
        "auth_algo": ["sha1-hmac", "sha2-224-hmac", "sha2-256-hmac",
                      "sha2-384-hmac", "sha2-512-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [20, 28, 32, 48],
        "output_cipher": "470c43ce135176ff34300c11b8a5dc463be774851c405eb67a3c54e\
30707b6ac47b1dca58d5a2dab1dee452f7712f1803709d100608f8df9786156e4656ff60cb6a2f722\
e6a96932fa0dbba8c4941e61b8ca2b5903bc724d5f68856b9e6f66d7b4e42cc49b44bb85b7ce2f1c5\
21e1a2719a47097922e0b627bbee2918ac5c5caf84d9e62d772fc676d3bce0bb17b95cb5e1477da05\
1aebbdbbf2a7037237a3537c738aadbfff3d3f2b3be5ddbcc7213e265705224961adf48f8df3ba8a8\
fc2ab337f7031a0f20636c82074a6bebcf91f06e04d45fa1dcc8454b6be54e53e3f9c99f0f830b16a\
7a452e75e15894bf869fc585090c8c4bfbdb9f2a6246f4308300",
        "output_hash": "*"
    },

    "qat_snow3g_00": {
        "vdev": "",
        "chain": ["CIPHER_ONLY", "HASH_ONLY"],
        "cdev_type": "HW",
        "cipher_algo": ["snow3g-uea2"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16],
        "iv": [16],
        "auth_algo": ["snow3g-uia2"],
        "auth_op": ["GENERATE"],
        "auth_key": [16],
        "auth_key_random_size": "",
        "aad": [16],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [4],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "qat_kasumi_00": {
        "vdev": "",
        "chain": ["CIPHER_ONLY", "HASH_ONLY"],
        "cdev_type": "HW",
        "cipher_algo": ["kasumi-f8"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16],
        "iv": [8],
        "auth_algo": ["kasumi-f9"],
        "auth_op": ["GENERATE"],
        "auth_key": [16],
        "auth_key_random_size": "",
        "aad": "",
        "aad_random_size": "",
        "input": [256],
        "digest_size": [4],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "qat_zuc_00": {
        "vdev": "",
        "chain": ["CIPHER_ONLY", "HASH_ONLY"],
        "cdev_type": "HW",
        "cipher_algo": ["zuc-eea3"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16],
        "iv": [16],
        "auth_algo": ["zuc-eia3"],
        "auth_op": ["GENERATE"],
        "auth_key": [16],
        "auth_key_random_size": "",
        "aad": [16],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [4],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "qat_NULL_auto": {
        "vdev": "",
        "chain": ["CIPHER_ONLY", "HASH_ONLY", "CIPHER_HASH"],
        "cdev_type": "HW",
        "cipher_algo": ["null"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [0],
        "iv": "",
        "auth_algo": ["null"],
        "auth_op": ["GENERATE"],
        "auth_key": [0],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "digest": "",
        "input": [256],
        "digest_size": "",
        "output_cipher": "*",
        "output_hash": "*"
    },

    "aesni_mb_AES_CBC_00": {
        "vdev": "crypto_aesni_mb",
        "chain": ["CIPHER_ONLY", "CIPHER_HASH"],
        "cdev_type": "SW",
        "cipher_algo": ["aes-cbc"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16, 24, 32],
        "iv": [16],
        "auth_algo": ["sha1-hmac", "sha2-256-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [12, 16],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "aesni_mb_AES_CTR_00": {
        "vdev": "crypto_aesni_mb",
        "chain": ["CIPHER_ONLY", "CIPHER_HASH"],
        "cdev_type": "SW",
        "cipher_algo": ["aes-ctr"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16],
        "iv": [16],
        "auth_algo": ["sha1-hmac", "sha2-256-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [12, 16],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "aesni_mb_hash_00": {
        "vdev": "crypto_aesni_mb",
        "chain": ["HASH_ONLY"],
        "cdev_type": "SW",
        "cipher_algo": "",
        "cipher_op": "",
        "cipher_key": "",
        "iv": "",
        "auth_algo": ["md5-hmac", "sha1-hmac", "sha2-224-hmac", "sha2-256-hmac",
                      "sha2-384-hmac", "sha2-512-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [12, 14, 16, 24],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "aesni_mb_AES_CCM_00": {
        "vdev": "crypto_aesni_mb",
        "chain": ["AEAD"],
        "cdev_type": "SW",
        "cipher_algo": ["aes-ccm"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16],
        "iv": [7, 8, 9, 10 ,11, 12, 13],
        "auth_algo": ["aes-ccm"],
        "auth_op": ["GENERATE"],
        "auth_key": [16],
        "auth_key_random_size": "",
        "aad": [8],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [8, 16],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "aesni_mb_3DES_CBC_00": {
        "vdev": "crypto_aesni_mb",
        "chain": ["CIPHER_ONLY", "CIPHER_HASH"],
        "cdev_type": "SW",
        "cipher_algo": ["3des-cbc"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [8, 16, 24],
        "iv": [8],
        "auth_algo": ["sha1-hmac", "sha2-256-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [0, 64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [12, 16],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "aesni_mb_h_MD_SHA_00": {
        "vdev": "crypto_aesni_mb",
        "chain": ["HASH_ONLY"],
        "cdev_type": "SW",
        "cipher_algo": "",
        "cipher_op": "",
        "cipher_key": "",
        "iv": "",
        "auth_algo": ["md5-hmac", "sha1-hmac", "sha2-224-hmac", "sha2-256-hmac",
                      "sha2-384-hmac", "sha2-512-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [0, 64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [12, 14, 16, 24],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "aesni_mb_aead_AES_GCM_00": {
        "vdev": "crypto_aesni_mb",
        "chain": ["AEAD"],
        "cdev_type": "SW",
        "cipher_algo": ["aes-gcm"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16, 24, 32],
        "iv": [12],
        "auth_algo": ["aes-gcm"],
        "auth_op": "",
        "auth_key": "",
        "auth_key_random_size": "",
        "aad": [16],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [8, 16],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "null_NULL_auto": {
        "vdev": "crypto_null",
        "chain": ["CIPHER_ONLY", "HASH_ONLY", "CIPHER_HASH"],
        "cdev_type": "SW",
        "cipher_algo": ["null"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [0],
        "iv": [0],
        "auth_algo": ["null"],
        "auth_op": ["GENERATE"],
        "auth_key": [0],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "digest": "",
        "input": [256],
        "digest_size": "",
        "output_cipher": "*",
        "output_hash": "*"
    },

    "aesni_gcm_aead_AES_GCM_01": {
        "vdev": "crypto_aesni_gcm",
        "chain": ["AEAD"],
        "cdev_type": "SW",
        "cipher_algo": ["aes-gcm"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16, 24, 32],
        "iv": [12],
        "auth_algo": ["aes-gcm", "aes-gmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [16],
        "auth_key_random_size": "",
        "aad": [16],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [8, 16],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "aesni_gcm_aead_AES_CCM_01": {
        "vdev": "crypto_aesni_gcm",
        "chain": ["AEAD"],
        "cdev_type": "SW",
        "cipher_algo": ["aes-ccm"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16],
        "iv": [12],
        "auth_algo": ["aes-ccm"],
        "auth_op": ["GENERATE"],
        "auth_key": [16],
        "auth_key_random_size": "",
        "aad": [16],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [8, 16],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "kasumi_kasumi_00": {
        "vdev": "crypto_kasumi",
        "chain": ["CIPHER_ONLY", "HASH_ONLY"],
        "cdev_type": "SW",
        "cipher_algo": ["kasumi-f8"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16],
        "iv": [8],
        "auth_algo": ["kasumi-f9"],
        "auth_op": ["GENERATE"],
        "auth_key": [16],
        "auth_key_random_size": "",
        "aad": "",
        "aad_random_size": "",
        "input": [256],
        "digest_size": [4],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "snow3g_snow3g_00": {
        "vdev": "crypto_snow3g",
        "chain": ["CIPHER_ONLY", "HASH_ONLY"],
        "cdev_type": "SW",
        "cipher_algo": ["snow3g-uea2"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16],
        "iv": [16],
        "auth_algo": ["snow3g-uia2"],
        "auth_op": ["GENERATE"],
        "auth_key": [16],
        "auth_key_random_size": "",
        "aad": [16],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [4],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "zuc_zuc_00": {
        "vdev": "crypto_zuc",
        "chain": ["CIPHER_ONLY", "HASH_ONLY"],
        "cdev_type": "SW",
        "cipher_algo": ["zuc-eea3"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16],
        "iv": [16],
        "auth_algo": ["zuc-eia3"],
        "auth_op": ["GENERATE"],
        "auth_key": [16],
        "auth_key_random_size": "",
        "aad": [16],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [4],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "openssl_3DES_CBC_00": {
        "vdev": "crypto_openssl",
        "chain": ["CIPHER_ONLY", "CIPHER_HASH"],
        "cdev_type": "SW",
        "cipher_algo": ["3des-cbc"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [8, 16, 24],
        "iv": [8],
        "auth_algo": ["sha1-hmac", "sha2-256-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [0, 64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [20, 28],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "openssl_3DES_CTR_00": {
        "vdev": "crypto_openssl",
        "chain": ["CIPHER_ONLY", "CIPHER_HASH"],
        "cdev_type": "SW",
        "cipher_algo": ["3des-ctr"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [24],
        "iv": [8],
        "auth_algo": ["sha1-hmac", "sha2-256-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [0, 64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [20, 28],
        "output_cipher": "470c43ce135176ff34300c11b8a5dc463be774851c405eb67a3c54e\
30707b6ac47b1dca58d5a2dab1dee452f7712f1803709d100608f8df9786156e4656ff60cb6a2f722\
e6a96932fa0dbba8c4941e61b8ca2b5903bc724d5f68856b9e6f66d7b4e42cc49b44bb85b7ce2f1c5\
21e1a2719a47097922e0b627bbee2918ac5c5caf84d9e62d772fc676d3bce0bb17b95cb5e1477da05\
1aebbdbbf2a7037237a3537c738aadbfff3d3f2b3be5ddbcc7213e265705224961adf48f8df3ba8a8\
fc2ab337f7031a0f20636c82074a6bebcf91f06e04d45fa1dcc8454b6be54e53e3f9c99f0f830b16a\
7a452e75e15894bf869fc585090c8c4bfbdb9f2a6246f4308300",
        "output_hash": "*"
    },

    "openssl_AES_CBC_00": {
        "vdev": "crypto_openssl",
        "chain": ["CIPHER_ONLY", "CIPHER_HASH"],
        "cdev_type": "SW",
        "cipher_algo": ["aes-cbc"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16, 24, 32],
        "iv": [16],
        "auth_algo": ["sha1-hmac", "sha2-256-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [20, 28],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "openssl_AES_CTR_00": {
        "vdev": "crypto_openssl",
        "chain": ["CIPHER_ONLY", "CIPHER_HASH"],
        "cdev_type": "SW",
        "cipher_algo": ["aes-ctr"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16, 24, 32],
        "iv": [16],
        "auth_algo": ["sha1-hmac", "sha2-256-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [20, 28],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "openssl_AES_GCM_00": {
        "vdev": "crypto_openssl",
        "chain": ["AEAD"],
        "cdev_type": "SW",
        "cipher_algo": ["aes-gcm"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16, 24, 32],
        "iv": [12],
        "auth_algo": ["aes-gcm"],
        "auth_op": ["GENERATE"],
        "auth_key": [16],
        "auth_key_random_size": "",
        "aad": [16],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [16],
        "digest_size": [16],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "openssl_AES_CCM_00": {
        "vdev": "crypto_openssl",
        "chain": ["AEAD"],
        "cdev_type": "SW",
        "cipher_algo": ["aes-ccm"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16, 24, 32],
        "iv": [12],
        "auth_algo": ["aes-ccm"],
        "auth_op": ["GENERATE"],
        "auth_key": [16],
        "auth_key_random_size": "",
        "aad": [16],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [8, 16],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "openssl_h_MD_SHA_00": {
        "vdev": "crypto_openssl",
        "chain": ["HASH_ONLY"],
        "cdev_type": "SW",
        "cipher_algo": "",
        "cipher_op": "",
        "cipher_key": "",
        "iv": "",
        "auth_algo": ["md5-hmac", "sha1-hmac", "sha2-224-hmac", "sha2-256-hmac",
                      "sha2-384-hmac", "sha2-512-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [0, 64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [16, 20, 28, 48, 64],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "qat_AES_DOCSISBPI_01": {
        "vdev": "",
        "chain": ["CIPHER_ONLY"],
        "cdev_type": "HW",
        "cipher_algo": "aes-docsisbpi",
        "cipher_op": ["ENCRYPT"],
        "cipher_key": "e6600fd8852ef5abe6600fd8852ef5ab",
        "iv": "810e528e1c5fda1a810e528e1c5fda1a",
        "auth_algo": "",
        "auth_op": "",
        "auth_key": "",
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": "000102030405060708090a0b0c0d0e91d2d19f",
        "digest_size": "",
        "output_cipher": "9dd1674bba61101b56756474364f101d44d473",
        "output_hash": "*"
    },

    "qat_DES_DOCSISBPI_01": {
        "vdev": "",
        "chain": ["CIPHER_ONLY"],
        "cdev_type": "HW",
        "cipher_algo": "des-docsisbpi",
        "cipher_op": ["ENCRYPT"],
        "cipher_key": "e6600fd8852ef5ab",
        "iv": "810e528e1c5fda1a",
        "auth_algo": "",
        "auth_op": "",
        "auth_key": "",
        "auth_key_random_size": "",
        "aad": "",
        "aad_random_size": "",
        "input": "000102030405060708090a0b0c0d0e910001020304050607d2d19f",
        "digest_size": "",
        "output_cipher": "0dda5acbd05e5567514746868a71e577bdb2125f9f72be230e9fb2",
        "output_hash": "*"
    },

    "aesni_mb_AES_DOCSISBPI_01": {
        "vdev": "crypto_aesni_mb",
        "chain": ["CIPHER_ONLY"],
        "cdev_type": "SW",
        "cipher_algo": "aes-docsisbpi",
        "cipher_op": ["ENCRYPT"],
        "cipher_key": "e6600fd8852ef5abe6600fd8852ef5ab",
        "iv": "810e528e1c5fda1a810e528e1c5fda1a",
        "auth_algo": "",
        "auth_op": "",
        "auth_key": "",
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": "000102030405060708090a0b0c0d0e91d2d19f",
        "digest_size": "",
        "output_cipher": "9dd1674bba61101b56756474364f101d44d473",
        "output_hash": "*"
    },

    "openssl_DES_DOCSISBPI_01": {
        "vdev": "crypto_openssl",
        "chain": ["CIPHER_ONLY"],
        "cdev_type": "SW",
        "cipher_algo": "des-docsisbpi",
        "cipher_op": ["ENCRYPT"],
        "cipher_key": "e6600fd8852ef5ab",
        "iv": "810e528e1c5fda1a",
        "auth_algo": "",
        "auth_op": "",
        "auth_key": "",
        "auth_key_random_size": "",
        "aad": "",
        "aad_random_size": "",
        "input": "000102030405060708090a0b0c0d0e910001020304050607d2d19f",
        "digest_size": "",
        "output_cipher": "0dda5acbd05e5567514746868a71e577bdb2125f9f72be230e9fb2",
        "output_hash": "*"
    },

    "aesni_mb_DES_DOCSISBPI_01": {
        "vdev": "crypto_aesni_mb",
        "chain": ["CIPHER_ONLY"],
        "cdev_type": "SW",
        "cipher_algo": "des-docsisbpi",
        "cipher_op": ["ENCRYPT"],
        "cipher_key": "e6600fd8852ef5ab",
        "iv": "810e528e1c5fda1a",
        "auth_algo": "",
        "auth_op": "",
        "auth_key": "",
        "auth_key_random_size": "",
        "aad": "",
        "aad_random_size": "",
        "input": "000102030405060708090a0b0c0d0e910001020304050607d2d19f",
        "digest_size": "",
        "output_cipher": "0dda5acbd05e5567514746868a71e577bdb2125f9f72be230e9fb2",
        "output_hash": "*"
    },

    "aesni_mb_DES_CBC_00": {
        "vdev": "crypto_aesni_mb",
        "chain": ["CIPHER_ONLY", "CIPHER_HASH"],
        "cdev_type": "SW",
        "cipher_algo": ["des-cbc"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [8],
        "iv": [8],
        "auth_algo": ["sha1-hmac", "sha2-256-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [12, 16],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "openssl_DES_CBC_00": {
        "vdev": "crypto_openssl",
        "chain": ["CIPHER_ONLY", "CIPHER_HASH"],
        "cdev_type": "SW",
        "cipher_algo": ["des-cbc"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [8],
        "iv": [8],
        "auth_algo": ["sha1-hmac", "sha2-256-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [20, 28],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "scheduler_AES_CBC_00": {
        "vdev": "crypto_scheduler",
        "chain": ["CIPHER_HASH"],
        "cdev_type": "ANY",
        "cipher_algo": ["aes-cbc"],
        "cipher_op": ["ENCRYPT", "DECRYPT"],
        "cipher_key": [16],
        "iv": [16],
        "auth_algo": ["sha1-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [64],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [20, 32],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "scheduler_AES_GCM_00": {
        "vdev": "crypto_scheduler",
        "chain": ["AEAD"],
        "cdev_type": "ANY",
        "cipher_algo": ["aes-gcm"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [16, 24, 32],
        "iv": [12],
        "auth_algo": ["aes-gcm"],
        "auth_op": ["GENERATE"],
        "auth_key": [16],
        "auth_key_random_size": "",
        "aad": [16],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [16],
        "output_cipher": "*",
        "output_hash": "*"
    },

    "qat_AES_XTS_00": {
        "vdev": "",
        "chain": ["CIPHER_ONLY", "CIPHER_HASH"],
        "cdev_type": "HW",
        "cipher_algo": ["aes-xts"],
        "cipher_op": ["ENCRYPT"],
        "cipher_key": [32],
        "iv": [16],
        "auth_algo": ["sha1-hmac", "sha2-256-hmac"],
        "auth_op": ["GENERATE"],
        "auth_key": [64, 128],
        "auth_key_random_size": "",
        "aad": [0],
        "aad_random_size": "",
        "input": [256],
        "digest_size": [20, 32],
        "output_cipher": "*",
        "output_hash": "*"
    },
}
