.. Copyright (c) <2017>, Intel Corporation
      All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

   - Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.

   - Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in
     the documentation and/or other materials provided with the
     distribution.

   - Neither the name of Intel Corporation nor the names of its
     contributors may be used to endorse or promote products derived
     from this software without specific prior written permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPR   ESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
   COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
   STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
   OF THE POSSIBILITY OF SUCH DAMAGE.

==========================
Niantic Inline IPsec Tests
==========================

This test plan describe the method of validation inline hardware acceleration
of symmetric crypto processing of IPsec flows on Intel® 82599 10 GbE
Controller (IXGBE) within the cryptodev framework.

***Limitation:
AES-GCM 128 ESP Tunnel/Transport mode and Authentication only mode are
supported.***

Ref links:
https://tools.ietf.org/html/rfc4301

https://tools.ietf.org/html/rfc4302

https://tools.ietf.org/html/rfc4303

http://dpdk.org/doc/guides/sample_app_ug/ipsec_secgw.html

Abbr:
ESP: Encapsulating Security Payload::

	 0                   1                   2                   3
	 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ ----
	|               Security Parameters Index (SPI)                 | ^Int.
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ |Cov-
	|                      Sequence Number                          | |ered
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ | ----
	|                    Payload Data* (variable)                   | |   ^
	~                                                               ~ |   |
	|                                                               | |Conf.
	+               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ |Cov-
	|               |     Padding (0-255 bytes)                     | |ered*
	+-+-+-+-+-+-+-+-+               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ |   |
	|                               |  Pad Length   | Next Header   | v   v
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ ------
	|         Integrity Check Value-ICV   (variable)                |
	~                                                               ~
	|                                                               |
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


SPI: Security Parameters Index

The SPI is an arbitrary 32-bit value that is used by a receiver to identify
the SA to which an incoming packet is bound.

Sequence Number:

This unsigned 32-bit field contains a counter value that increases by
one for each packet sent

AES: Advanced Encryption Standard

GCM: Galois Counter Mode

Prerequisites
=============
2 *  10Gb Ethernet ports of the DUT are directly connected in full-duplex to
different ports of the peer traffic generator.

Bind two ports to vfio-pci.
modprobe vfio-pci

	
Test Case: Inline cfg parsing
=============================
Create inline ipsec configuration file like below::

	#SP IPv4 rules
	sp ipv4 out esp protect 1005 pri 1 dst 192.168.105.0/24 sport 0:65535 dport 0:65535

	#SA rules
	sa out 1005 aead_algo aes-128-gcm aead_key 2b:7e:15:16:28:ae:d2:a6:ab:f7:15:88:09:cf:4f:3d:de:ad:be:ef \
	mode ipv4-tunnel src 172.16.1.5 dst 172.16.2.5 \
	port_id 1 \
	type inline-crypto-offload \

	sa in 5 aead_algo aes-128-gcm aead_key 2b:7e:15:16:28:ae:d2:a6:ab:f7:15:88:09:cf:4f:3d:de:ad:be:ef \
	mode ipv4-tunnel src 172.16.1.5 dst 172.16.2.5 \
	port_id 1 \
	type inline-crypto-offload \

	#Routing rules
	rt ipv4 dst 172.16.2.5/32 port 1
	rt ipv4 dst 192.168.105.10/32 port 0

Starting ipsec-secgw sample and make sure SP/SA/RT rules loaded successfully.

Check ipsec-secgw can detect invalid cipher algo.

Check ipsec-secgw can detect invalid auth algo.

Check ipsec-secgw can detect invalid key format.


Test Case: IPSec Encryption
===========================
Start ipsec-secgw with two 82599 ports and assign port 1 to unprotected mode::

	sudo ./build/ipsec-secgw -l 20,21 -w 83:00.0 -w 83:00.1 --vdev 
	"crypto_null" --log-level 8 --socket-mem 1024,1 -- -p 0xf -P -u 
	0x2 --config="(0,0,20),(1,0,21)" -f ./enc.cfg

Use scapy to listen on unprotected port::

    sniff(iface='%s',count=1,timeout=10)
	
Use scapy send burst(32) normal packets with dst ip (192.168.105.0) to protected port.

Check burst esp packets received from unprotected port::

    tcpdump -Xvvvi ens802f1
    tcpdump: listening on ens802f1, link-type EN10MB (Ethernet), capture size 262144 bytes
    06:10:25.674233 IP (tos 0x0, ttl 64, id 0, offset 0, flags [none], proto ESP (50), length 108)
    172.16.1.5 > 172.16.2.5: ESP(spi=0x000003ed,seq=0x9), length 88
        0x0000:  4500 006c 0000 0000 4032 1f36 ac10 0105  E..l....@2.6....
        0x0010:  ac10 0205 0000 03ed 0000 0009 0000 0000  ................
        0x0020:  0000 0009 4468 a4af 5853 7545 b21d 977c  ....Dh..XSuE...|
        0x0030:  b911 7ec6 74a0 3349 b986 02d2 a322 d050  ..~.t.3I.....".P
        0x0040:  8a0d 4ffc ef4d 6246 86fe 26f0 9377 84b5  ..O..MbF..&..w..
        0x0050:  8b06 c7e0 05d3 1ac5 1a30 1a93 8660 4292  .........0...`B.
        0x0060:  999a c84d 49ed ff95 89a1 6917            ...MI.....i.

Check esp packets' format is correct.

See decrypted packets on scapy output::

    ###[ IP ]###
      version   = 4
      ihl       = 5
      tos       = 0x0
      len       = 52
      id        = 1
      flags     =
      frag      = 0
      ttl       = 63
      proto     = ip
      chksum    = 0x2764
      src       = 192.168.105.10
      dst       = 192.168.105.10
      \options   \
    ###[ Raw ]###
         load      = '|->test-test-test-test-test-t<-|'


Test Case: IPSec Encryption with Jumboframe
===========================================
Start ipsec-secgw with two 82599 ports and assign port 1 to unprotected mode::

	sudo ./build/ipsec-secgw -l 20,21 -w 83:00.0 -w 83:00.1 --vdev 
	"crypto_null" --log-level 8 --socket-mem 1024,1 -- -p 0xf -P -u 
	0x2 --config="(0,0,20),(1,0,21)" -f ./enc.cfg

Use scapy to listen on unprotected port 

Default frame size is 1518, send burst(1000) packets with dst ip (192.168.105.0) to protected port.

Check burst esp packets received from unprotected port.

Check esp packets' format is correct.

See decrypted packets on scapy output

Send burst(8192) jumbo packets with dst ip (192.168.105.0) to protected port.

Check burst esp packets can't be received from unprotected port.

Set jumbo frames size as 9000, start it with port 1 assigned to unprotected mode::

	sudo ./build/ipsec-secgw -l 20,21 -w 83:00.0 -w 83:00.1 --vdev 
	"crypto_null" --log-level 8 --socket-mem 1024,1 -- -p 0xf -P -u 
	0x2 -j 9000 --config="(0,0,20),(1,0,21)" -f ./enc.cfg

Use scapy to listen on unprotected port 
	
Send burst(8192) jumbo packets with dst ip (192.168.105.0) to protected port.

Check burst jumbo packets received from unprotected port.

Check esp packets' format is correct.

See decrypted packets on scapy output

Send burst(9000) jumbo packets with dst ip (192.168.105.0) to protected port.

Check burst jumbo packets can't be received from unprotected port.


Test Case: IPSec Encryption with RSS
====================================
Create configuration file with multiple SP/SA/RT rules for different ip address.

Start ipsec-secgw with two queues enabled on each port and port 1 assigned to unprotected mode::

	sudo ./build/ipsec-secgw -l 20,21 -w 83:00.0 -w 83:00.1 --vdev 
	"crypto_null" --log-level 8 --socket-mem 1024,1 -- -p 0xf -P -u 
	0x2 --config="(0,0,20),(0,1,20),(1,0,21),(1,1,21)" -f ./enc_rss.cfg

Use scapy to listen on unprotected port 
	
Send burst(32) packets with different dst ip to protected port.

Check burst esp packets received from queue 0 and queue 1 on unprotected port.
tcpdump -Xvvvi ens802f1

Check esp packets' format is correct.

See decrypted packets on scapy output


Test Case: IPSec Decryption
===========================
Start ipsec-secgw with two 82599 ports and assign port 1 to unprotected mode::

	sudo ./build/ipsec-secgw -l 20,21 -w 83:00.0 -w 83:00.1 --vdev 
	"crypto_null" --log-level 8 --socket-mem 1024,1 -- -p 0xf -P -u 
	0x2 --config="(0,0,20),(1,0,21)" -f ./dec.cfg

Send two burst(32) esp packets to unprotected port.

First one will produce an error "IPSEC_ESP: failed crypto op" in the IPsec application, 
but it will setup the SA. Second one will decrypt and send back the decrypted packet.

Check burst packets which have been decapsulated received from protected port
tcpdump -Xvvvi ens802f0

Test Case: IPSec Decryption with wrong key
==========================================
Start ipsec-secgw with two 82599 ports and assign port 1 to unprotected mode::

	sudo ./build/ipsec-secgw -l 20,21 -w 83:00.0 -w 83:00.1 --vdev 
	"crypto_null" --log-level 8 --socket-mem 1024,1 -- -p 0xf -P -u 
	0x2 --config="(0,0,20),(1,0,21)" -f ./dec.cfg

Change dec.cfg key is not same with send packet encrypted key
	
Send one burst(32) esp packets to unprotected port.

IPsec application will produce an error "IPSEC_ESP: failed crypto op" , 
but it will setup the SA. 

Send one burst(32) esp packets to unprotected port.

Check burst packets which have been decapsulated can't be received from protected port,
IPsec application will produce error "IPSEC_ESP: failed crypto op".


Test Case: IPSec Decryption with Jumboframe
===========================================
Start ipsec-secgw with two 82599 ports and assign port 1 to unprotected mode::
	sudo ./build/ipsec-secgw -l 20,21 -w 83:00.0 -w 83:00.1 --vdev 
	"crypto_null" --log-level 8 --socket-mem 1024,1 -- -p 0xf -P -u 
	0x2 --config="(0,0,20),(1,0,21)" -f ./dec.cfg

Default frame size is 1518, Send two burst(1000) esp packets to unprotected port.

First one will produce an error "IPSEC_ESP: failed crypto op" in the IPsec application, 
but it will setup the SA. Second one will decrypt and send back the decrypted packet.

Check burst(1000) packets which have been decapsulated received from protected port.

Send burst(8192) esp packets to unprotected port.

Check burst(8192) packets which have been decapsulated can't be received from protected port.

Set jumbo frames size as 9000, start it with port 1 assigned to unprotected mode::

	sudo ./build/ipsec-secgw -l 20,21 -w 83:00.0 -w 83:00.1 --vdev 
	"crypto_null" --log-level 8 --socket-mem 1024,1 -- -p 0xf -P -u 
	0x2 -j 9000 --config="(0,0,20),(1,0,21)" -f ./dec.cfg

Send two burst(8192) esp packets to unprotected port.

First one will produce an error "IPSEC_ESP: failed crypto op" in the IPsec application, 
but it will setup the SA. Second one will decrypt and send back the decrypted packet.

Check burst(8192) packets which have been decapsulated received from protected port.

Send burst(9000) esp packets to unprotected port.

Check burst(9000) packets which have been decapsulated can't be received from protected port.


Test Case: IPSec Decryption with RSS
====================================
Create configuration file with multiple SA rule for different ip address.

Start ipsec-secgw with two 82599 ports and assign port 1 to unprotected mode::

	sudo ./build/ipsec-secgw -l 20,21 -w 83:00.0 -w 83:00.1 --vdev 
	"crypto_null" --log-level 8 --socket-mem 1024,1 -- -p 0xf -P -u 
	0x2 -config="(0,0,20),(0,1,20),(1,0,21),(1,1,21)" -f ./dec_rss.cfg

Send two burst(32) esp packets with different ip to unprotected port.

First one will produce an error "IPSEC_ESP: failed crypto op" in the IPsec application, 
but it will setup the SA. Second one will decrypt and send back the decrypted packet.

Check burst(32) packets which have been decapsulated received from queue 0 and
1 on protected port.


Test Case: IPSec Encryption/Decryption simultaneously
=====================================================
Start ipsec-secgw with two 82599 ports and assign port 1 to unprotected mode::

	sudo ./build/ipsec-secgw -l 20,21 -w 83:00.0 -w 83:00.1 
        --vdev "crypto_null" --log-level 8 --socket-mem 1024,1 
        -- -p 0xf -P -u 0x2 --config="(0,0,20),(1,0,21)" -f ./enc_dec.cfg
	
Send normal and esp packets to protected and unprotected ports simultaneously.

Note when testing inbound IPSec, first one will produce an error "IPSEC_ESP: 
invalid padding" in the IPsec application, but it will setup the SA. Second 
one will decrypt and send back the decrypted packet.

Check esp and normal packets received from unprotected and protected ports.
