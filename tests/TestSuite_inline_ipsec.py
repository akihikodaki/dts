# BSD LICENSE
#
# Copyright(c) 2010-2018 Intel Corporation. All rights reserved.
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
Test inline_ipsec.
"""

import utils
import time
import re
import random

from scapy.all import ESP, IP, Ether, sendp, SecurityAssociation
from test_case import TestCase

ETHER_STANDARD_MTU = 1518
ETHER_JUMBO_FRAME_MTU = 9000


class TestInlineIpsec(TestCase):
    """
    This suite depend PyCryptodome,it provide authenticated encryption modes(GCM)
    my environment:cryptography (1.7.2), pycryptodome (3.4.7), pycryptodomex (3.4.7),
    pycryptopp (0.6.0.1206569328141510525648634803928199668821045408958), scapy (2.4.2)
    """

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.verify(self.nic in ["niantic"], "%s NIC not support" % self.nic)
        self.verify(self.drivername in ["vfio-pci"], "%s drivername not support" % self.drivername)
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        cores = self.dut.get_core_list("1S/4C/1T")
        self.coremask = utils.create_mask(cores)

        # get test port info
        self.rxport = self.tester.get_local_port(1)
        self.txport = self.tester.get_local_port(0)
        self.rxItf = self.tester.get_interface(self.rxport)
        self.txItf = self.tester.get_interface(self.txport)

        self.rx_src = self.tester.get_mac(self.rxport)
        self.tx_dst = self.dut.get_mac_address(self.dut_ports[0])

        # get dut port pci
        self.portpci_0 = self.dut.get_port_pci(self.dut_ports[0])
        self.portpci_1 = self.dut.get_port_pci(self.dut_ports[1])

        # enable tester mtu
        self.rxnetobj = self.tester.ports_info[self.rxport]['port']
        self.rxnetobj.enable_jumbo(framesize=ETHER_JUMBO_FRAME_MTU + 100)
        self.txnetobj = self.tester.ports_info[self.txport]['port']
        self.txnetobj.enable_jumbo(framesize=ETHER_JUMBO_FRAME_MTU + 100)

        self.path = "./examples/ipsec-secgw/build/ipsec-secgw"
        # add print code in IPSEC app
        sedcmd = r"""sed -i -e 's/if (nb_rx > 0)/if (nb_rx > 0) {/g' -e '/\/\* dequeue and process completed crypto-ops \*\//i\\t\t\t}' -e '/process_pkts(qconf, pkts, nb_rx, portid);/i\\t\t\t\tprintf("[debug]receive %hhu packet in rxqueueid=%hhu\\n",nb_rx, queueid);' examples/ipsec-secgw/ipsec-secgw.c"""
        self.dut.send_expect(sedcmd, "#", 60)

        # build sample app
        out = self.dut.build_dpdk_apps("./examples/ipsec-secgw")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

        self.cfg_prepare()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def cfg_prepare(self):
        """
        write the inline_ipsec configuration file
        """
        enc = (
            "#SP IPv4 rules\n"
            "sp ipv4 out esp protect 1005 pri 1 dst 192.168.105.0/24 sport 0:65535 dport 0:65535\n"
            "#SA rules\n"
            "sa out 1005 aead_algo aes-128-gcm aead_key 2b:7e:15:16:28:ae:d2:a6:ab:f7:15:88:09:cf:4f:3d:de:ad:be:ef mode ipv4-tunnel src 172.16.1.5 dst 172.16.2.5 port_id 1 type inline-crypto-offload\n"
            "#Routing rules\n"
            "rt ipv4 dst 172.16.2.5/32 port 1\n")

        dec = (
            "#SA rules\n"
            "sa in 5 aead_algo aes-128-gcm aead_key 2b:7e:15:16:28:ae:d2:a6:ab:f7:15:88:09:cf:4f:3d:de:ad:be:ef mode ipv4-tunnel src 172.16.1.5 dst 172.16.2.5 port_id 1 type inline-crypto-offload \n"
            "#Routing rules\n"
            "rt ipv4 dst 192.168.105.10/32 port 0\n"
        )
        enc_rss = (
            "#SP IPv4 rules\n"
            "sp ipv4 out esp protect 1002 pri 1 dst 192.168.102.0/24 sport 0:65535 dport 0:65535\n"
            "sa out 1002 aead_algo aes-128-gcm aead_key 2b:7e:15:16:28:ae:d2:a6:ab:f7:15:88:09:cf:4f:3d:de:ad:be:ef mode ipv4-tunnel src 172.16.31.35 dst 172.16.32.35 port_id 1 type inline-crypto-offload \n"
            "#Routing rules\n"
            "rt ipv4 dst 172.16.32.35/32 port 1\n"
        )
        dec_rss = (
            "#SA rules\n"
            "sa in 3 aead_algo aes-128-gcm aead_key 2b:7e:15:16:28:ae:d2:a6:ab:f7:15:88:09:cf:4f:3d:de:ad:be:ef mode ipv4-tunnel src 172.16.21.25 dst 172.16.22.25 port_id 1 type inline-crypto-offload \n"
            "#Routing rules\n"
            "rt ipv4 dst 192.168.105.10/32 port 0\n"
        )
        dec_wrong_key = (
            "#SA rules\n"
            "sa in 5 aead_algo aes-128-gcm aead_key 2f:7e:15:16:28:ae:d2:a6:ab:f7:15:88:09:cf:4f:3d:de:ad:be:ef mode ipv4-tunnel src 172.16.1.5 dst 172.16.2.5 port_id 1 type inline-crypto-offload \n"
            "#Routing rules\n"
            "rt ipv4 dst 192.168.105.10/32 port 0\n"
        )
        enc_dec = (
            "#SP IPv4 rules\n"
            "sp ipv4 out esp protect 1005 pri 1 dst 192.168.105.0/24 sport 0:65535 dport 0:65535\n"
            "#SA rules\n"
            "sa out 1005 aead_algo aes-128-gcm aead_key 2b:7e:15:16:28:ae:d2:a6:ab:f7:15:88:09:cf:4f:3d:de:ad:be:ef mode ipv4-tunnel src 172.16.1.5 dst 172.16.2.5 port_id 1 type inline-crypto-offload \n"
            "sa in 5 aead_algo aes-128-gcm aead_key 2b:7e:15:16:28:ae:d2:a6:ab:f7:15:88:09:cf:4f:3d:de:ad:be:ef mode ipv4-tunnel src 172.16.1.5 dst 172.16.2.5 port_id 1 type inline-crypto-offload \n"
            "#Routing rules\n"
            "rt ipv4 dst 172.16.2.5/32 port 1\n"
            "rt ipv4 dst 192.168.105.10/32 port 0\n"
        )
        self.set_cfg('enc.cfg', enc)
        self.set_cfg('dec.cfg', dec)
        self.set_cfg('enc_rss.cfg', enc_rss)
        self.set_cfg('dec_rss.cfg', dec_rss)
        self.set_cfg('enc_dec.cfg', enc_dec)
        self.set_cfg('dec_wrong_key.cfg', dec_wrong_key)

    def set_cfg(self, filename, cfg):
        """
        open file and write cfg, scp it to dut base directory  
        """
        for i in cfg:
            with open(filename, 'w') as f:
                f.write(cfg)
        self.dut.session.copy_file_to(filename, self.dut.base_dir)

    def send_encryption_package(self, intf, paysize=64, do_encrypt=False, send_spi=5, count=1,
                                inner_dst='192.168.105.10', sa_src='172.16.1.5', sa_dst='172.16.2.5'):
        """
        prepare a packet and send
        """
        test = 'test-' * 2000
        payload = test[0:int(paysize)]
        sa_gcm = SecurityAssociation(ESP, spi=send_spi,
                                     crypt_algo='AES-GCM',
                                     crypt_key='\x2b\x7e\x15\x16\x28\xae\xd2\xa6\xab\xf7\x15\x88\x09\xcf\x4f\x3d\xde\xad\xbe\xef',
                                     auth_algo='NULL', auth_key=None,
                                     tunnel_header=IP(src=sa_src, dst=sa_dst))
        sa_gcm.crypt_algo.icv_size = 16

        p = IP(src='192.168.105.10', dst=inner_dst)
        p /= payload
        p = IP(str(p))

        if do_encrypt == True:
            print "send encrypt package"
            print("before encrypt, the package info is like below: ")
            p.show()
            e = sa_gcm.encrypt(p)
        else:
            print "send normal package"
            e = p

        eth_e = Ether() / e
        eth_e.src = self.rx_src
        eth_e.dst = self.tx_dst
        session_send = self.tester.create_session(
            name='send_encryption_package')
        sendp(eth_e, iface=intf, count=count)
        self.tester.destroy_session(session_send)
        return payload, p.src, p.dst

    def Ipsec_Encryption(self, config, file_name, txItf, rxItf, paysize=32, jumboframe=1518, do_encrypt=False,
                         verify=True, send_spi=5, receive_spi=1005, count=1, inner_dst='192.168.105.10',
                         sa_src='172.16.1.5', sa_dst='172.16.2.5'):
        """
        verify Ipsec receive package
        """
        cmd = self.path + " -l 20,21 -w %s -w %s --vdev 'crypto_null' --log-level 8 --socket-mem 1024,1024 -- -p 0xf -P -u 0x2 -j %s --config='%s' -f %s" % (
            self.portpci_0, self.portpci_1, jumboframe, config, file_name)
        self.dut.send_expect(cmd, "IPSEC", 60)

        session_receive = self.tester.create_session(
            name='receive_encryption_package')
        sa_gcm = r"sa_gcm=SecurityAssociation(ESP,spi=%s,crypt_algo='AES-GCM',crypt_key='\x2b\x7e\x15\x16\x28\xae\xd2\xa6\xab\xf7\x15\x88\x09\xcf\x4f\x3d\xde\xad\xbe\xef',auth_algo='NULL',auth_key=None,tunnel_header=IP(src='172.16.1.5',dst='172.16.2.5'))" % receive_spi

        session_receive.send_expect("scapy", ">>>", 10)
        time.sleep(1)
        session_receive.send_expect(
            "pkts=sniff(iface='%s',count=1,timeout=45)" % rxItf, "", 10)

        if do_encrypt:
            send_package = self.send_encryption_package(
                txItf, paysize, do_encrypt, send_spi, count, inner_dst, sa_src, sa_dst)
            time.sleep(45)
            session_receive.send_expect("pkts", "", 30)
            out = session_receive.send_expect("pkts[0]['IP'] ", ">>>", 10)
        else:
            session_receive2 = self.tester.create_session(name='receive_encryption_package2')
            session_receive2.send_expect("tcpdump -Xvvvi %s -c 1" % rxItf, "", 30)
            send_package = self.send_encryption_package(txItf, paysize, do_encrypt, send_spi, count, inner_dst, sa_src,
                                                        sa_dst)
            time.sleep(45)
            rev = session_receive2.get_session_before()
            print(rev)
            p = re.compile(': ESP\(spi=0x\w+,seq=0x\w+\),')
            res = p.search(rev)
            self.verify(res, 'encrypt failed, tcpdump get %s' % rev)
            self.tester.destroy_session(session_receive2)
            session_receive.send_expect("pkts", "", 30)
            session_receive.send_expect(sa_gcm, ">>>", 10)
            time.sleep(2)
            session_receive.send_expect("results=sa_gcm.decrypt(pkts[0]['IP'])", ">>>", 10)
            out = session_receive.send_expect("results", ">>>", 10)

        if verify:
            print('received packet content is %s' % out)
            print('send pkt src ip is %s, dst ip is %s, payload is %s' % (
                send_package[1], send_package[2], send_package[0]))
            self.verify(send_package[0] in out,
                        "Unreceived package or get other package")
        else:
            self.verify(send_package[0] not in out,
                        "The function is not in effect")
        session_receive.send_expect("quit()", "#", 10)
        self.tester.destroy_session(session_receive)

    def test_Ipsec_Encryption(self):
        """
        test Ipsec Encryption
        """
        config = '(0,0,21),(1,0,21)'
        paysize = random.randint(1, ETHER_STANDARD_MTU)
        self.Ipsec_Encryption(config, '/root/dpdk/enc.cfg',
                              self.txItf, self.rxItf, paysize)
        self.dut.send_expect("^C", "#", 5)

    def test_Ipsec_Encryption_Jumboframe(self):
        """
        test Ipsec Encryption Jumboframe
        """
        config = '(0,0,21),(1,0,21)'
        paysize = random.randint(ETHER_STANDARD_MTU, ETHER_JUMBO_FRAME_MTU)
        self.Ipsec_Encryption(config, '/root/dpdk/enc.cfg',
                              self.txItf, self.rxItf, paysize, ETHER_JUMBO_FRAME_MTU)
        self.dut.send_expect("^C", "#", 5)

    def test_Ipsec_Encryption_Rss(self):
        """
        test Ipsec Encryption Rss
        """
        config = '(0,0,20),(0,1,20),(1,0,21),(1,1,21)'
        self.Ipsec_Encryption(config, '/root/dpdk/enc_rss.cfg', self.txItf,
                              self.rxItf, send_spi=2, receive_spi=1002, inner_dst='192.168.102.10')
        out = self.dut.get_session_output()
        verifycode = "receive 1 packet in rxqueueid=1"
        self.verify(verifycode in out, "rxqueueid error")
        self.dut.send_expect("^C", "#", 5)

    def test_IPSec_Decryption(self):
        """
        test IPSec Decryption
        """
        config = '(0,0,21),(1,0,21)'
        paysize = random.randint(1, ETHER_STANDARD_MTU)
        self.Ipsec_Encryption(config, '/root/dpdk/dec.cfg', self.rxItf,
                              self.txItf, paysize, do_encrypt=True, count=2)
        self.dut.send_expect("^C", "#", 5)

    def test_IPSec_Decryption_Jumboframe(self):
        """
        test IPSec Decryption Jumboframe
        """
        config = '(0,0,21),(1,0,21)'
        paysize = random.randint(ETHER_STANDARD_MTU, ETHER_JUMBO_FRAME_MTU)
        self.Ipsec_Encryption(config, '/root/dpdk/dec.cfg', self.rxItf,
                              self.txItf, paysize, ETHER_JUMBO_FRAME_MTU, do_encrypt=True, count=2)
        self.dut.send_expect("^C", "#", 5)

    def test_Ipsec_Decryption_Rss(self):
        """
        test Ipsec Decryption Rss
        """
        config = '(0,0,20),(0,1,20),(1,0,21),(1,1,21)'
        self.Ipsec_Encryption(config, '/root/dpdk/dec_rss.cfg', self.rxItf, self.txItf, do_encrypt=True,
                              send_spi=3, receive_spi=1003, count=2, sa_src='172.16.21.25', sa_dst='172.16.22.25')
        out = self.dut.get_session_output()
        verifycode = "receive 1 packet in rxqueueid=1"
        self.verify(verifycode in out, "rxqueueid error")
        self.dut.send_expect("^C", "#", 5)

    def test_Ipsec_Decryption_wrongkey(self):
        """
        test Ipsec Decryption wrongkey
        """
        config = '(0,0,21),(1,0,21)'
        paysize = random.randint(1, ETHER_STANDARD_MTU)
        self.Ipsec_Encryption(config, '/root/dpdk/dec_wrong_key.cfg', self.rxItf,
                              self.txItf, paysize, do_encrypt=True, verify=False, count=2)
        out = self.dut.get_session_output()
        verifycode = "IPSEC_ESP: esp_inbound_post\(\) failed crypto op"
        l = re.findall(verifycode, out)
        self.verify(len(l) == 2, "Ipsec Decryption wrongkey failed")
        self.dut.send_expect("^C", "#", 5)

    def test_Ipsec_Encryption_Decryption(self):
        """
        test Ipsec Encryption Decryption
        """
        cmd = self.path + " -l 20,21 -w %s -w %s --vdev 'crypto_null' --log-level 8 --socket-mem 1024,1 -- -p 0xf -P -u 0x2 -j %s --config='%s' -f %s" % (
            self.portpci_0, self.portpci_1, '1518', '(0,0,21),(1,0,21)', '/root/dpdk/enc_dec.cfg')
        self.dut.send_expect(cmd, "IPSEC", 60)
        session_receive = self.tester.create_session(
            name='receive_encryption_package')
        sa_gcm = r"sa_gcm=SecurityAssociation(ESP, spi=1005,crypt_algo='AES-GCM',crypt_key='\x2b\x7e\x15\x16\x28\xae\xd2\xa6\xab\xf7\x15\x88\x09\xcf\x4f\x3d\xde\xad\xbe\xef',auth_algo='NULL', auth_key=None,tunnel_header=IP(src='172.16.1.5', dst='172.16.2.5'))"

        session_receive.send_expect("scapy", ">>>", 60)
        session_receive.send_expect(sa_gcm, ">>>", 60)
        session_receive.send_expect(
            "pkts=sniff(iface='%s',count=3,timeout=30)" % self.rxItf, "", 60)
        session_receive2 = self.tester.create_session(
            name='receive_encryption_package2')

        session_receive2.send_expect("scapy", ">>>", 60)
        session_receive2.send_expect(sa_gcm, ">>>", 60)
        session_receive2.send_expect(
            "pkts=sniff(iface='%s',count=2,timeout=30)" % self.txItf, "", 60)

        payload = "test for Ipsec Encryption Decryption simultaneously"
        sa_gcm = SecurityAssociation(ESP, spi=5,
                                     crypt_algo='AES-GCM',
                                     crypt_key='\x2b\x7e\x15\x16\x28\xae\xd2\xa6\xab\xf7\x15\x88\x09\xcf\x4f\x3d\xde\xad\xbe\xef',
                                     auth_algo='NULL', auth_key=None,
                                     tunnel_header=IP(src='172.16.1.5', dst='172.16.2.5'))
        sa_gcm.crypt_algo.icv_size = 16

        p = IP(src='192.168.105.10', dst='192.168.105.10')
        p /= payload
        p = IP(str(p))

        e1 = sa_gcm.encrypt(p)
        e2 = p

        eth_e1 = Ether() / e1
        eth_e1.src = self.rx_src
        eth_e1.dst = self.tx_dst
        eth_e2 = Ether() / e2
        eth_e2.src = self.rx_src
        eth_e2.dst = self.tx_dst
        session_receive3 = self.tester.create_session('check_forward_encryption_package')
        session_receive3.send_expect("tcpdump -Xvvvi %s -c 1" % self.rxItf, "", 30)
        time.sleep(2)
        sendp(eth_e1, iface=self.rxItf, count=2)
        sendp(eth_e2, iface=self.txItf, count=1)
        time.sleep(30)
        rev = session_receive3.get_session_before()
        print(rev)
        p = re.compile(': ESP\(spi=0x\w+,seq=0x\w+\),')
        res = p.search(rev)
        self.verify(res, 'encrypt failed, tcpdump get %s' % rev)
        session_receive.send_expect(
            "results=sa_gcm.decrypt(pkts[2]['IP'])", ">>>", 60)
        out = session_receive.send_expect("results", ">>>", 60)
        self.verify(payload in out,
                    "The package is not received. Please check the package")
        out = session_receive2.send_expect("pkts[1]", ">>>", 60)
        self.verify(payload in out,
                    "The package is not received. Please check the package")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.tester.send_expect("^C", "#", 5)
        self.dut.kill_all()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.rxnetobj.enable_jumbo(framesize=ETHER_STANDARD_MTU)
        self.txnetobj.enable_jumbo(framesize=ETHER_STANDARD_MTU)
