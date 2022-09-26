.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2016 Intel Corporation

=============================
IP Pipeline Application Tests
=============================

Description
===========
The "examples/ip_pipeline" application is the main DPDK Packet Framework
application.

The suit support NIC: Intel® Ethernet 700 Series(I40E_10G-SFP_XL710), Intel® Ethernet 800 Series(ICE_25G-E810C_SFP).

Prerequisites
==============
The DUT must have four 10G Ethernet ports connected to four ports on
Tester that are controlled by the Scapy packet generator::

    dut_port_0 <---> tester_port_0
    dut_port_1 <---> tester_port_1
    dut_port_2 <---> tester_port_2
    dut_port_3 <---> tester_port_3

Assume four DUT 10G Ethernet ports' pci device id is as the following::

    dut_port_0 : "0000:05:00.0"
    dut_port_1 : "0000:05:00.1"
    dut_port_2 : "0000:05:00.2"
    dut_port_3 : "0000:05:00.3"

Bind them to dpdk igb_uio driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0 05:00.1 05:00.2 05:00.3

Notes:
>>> if using trex as packet generator::

    trex>
    portattr --prom on -a
    service --port 1                                                                  1
    capture monitor start --rx 1 -v

The crypto cases need an IXIA as packet generator::

    dut_port_0 <---> IXIA_port_0

Change pci device id of LINK0 to pci device id of dut_port_0.
There are two drivers supported now: aesni_gcm and aesni_mb.
Different drivers support different Algorithms.

Build dpdk and examples=ip_pipeline:
   CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static <build_target>
   ninja -C <build_target>

   meson configure -Dexamples=ip_pipeline <build_target>
   ninja -C <build_target>

Test Case: l2fwd pipeline
===========================
1. Edit examples/ip_pipeline/examples/l2fwd.cli,
   change pci device id of LINK0, LINK1, LINK2, LINK3 to pci device id of
   dut_port_0, dut_port_1, dut_port_2, dut_port_3

2. Run ip_pipeline app as the following::

    ./<build_target>/examples/dpdk-ip_pipeline -c 0x3 -n 4 -- -s examples/l2fwd.cli

3. Send packets at tester side with scapy, verify:

   packets sent from tester_port_0 can be received at tester_port_1, and vice versa.
   packets sent from tester_port_2 can be received at tester_port_3, and vice versa.

Test Case: flow classification pipeline
=========================================
1. Edit examples/ip_pipeline/examples/flow.cli,
   change pci device id of LINK0, LINK1, LINK2, LINK3 to pci device id of
   dut_port_0, dut_port_1, dut_port_2, dut_port_3

2. Run ip_pipeline app as the following::

    ./<build_target>/examples/dpdk-ip_pipeline -c 0x3 -n 4 –- -s examples/flow.cli

3. Send following packets with one test port::

    packet_1:Ether(dst="00:11:22:33:44:55")/IP(src="100.0.0.10",dst="200.0.0.10")/TCP(sport=100,dport=200)/Raw(load="X"*6)
    packet_2:Ether(dst="00:11:22:33:44:55")/IP(src="100.0.0.11",dst="200.0.0.11")/TCP(sport=101,dport=201)/Raw(load="X"*6)
    packet_3:Ether(dst="00:11:22:33:44:55")/IP(src="100.0.0.12",dst="200.0.0.12")/TCP(sport=102,dport=202)/Raw(load="X"*6)
    packet_4:Ether(dst="00:11:22:33:44:55")/IP(src="100.0.0.13",dst="200.0.0.13")/TCP(sport=103,dport=203)/Raw(load="X"*6)

   Verify packet_1 was received by tester_port_0.
   Verify packet_2 was received by tester_port_1.
   Verify packet_3 was received by tester_port_2.
   Verify packet_4 was received by tester_port_3.

Test Case: routing pipeline
=============================
1. Edit examples/ip_pipeline/examples/route.cli,
   change pci device id of LINK0, LINK1, LINK2, LINK3 to pci device id of
   dut_port_0, dut_port_1, dut_port_2, dut_port_3.

2. Run ip_pipeline app as the following::

    ./<build_target>/examples/dpdk-ip_pipeline -c 0x3 -n 4 –- -s examples/route.cli,

3. Send following packets with one test port::

    packet_1:Ether(dst="00:11:22:33:44:55")/IP(dst="100.0.0.1")/Raw(load="X"*26)
    packet_2:Ether(dst="00:11:22:33:44:55")/IP(dst="100.64.0.1")/Raw(load="X"*26)
    packet_3:Ether(dst="00:11:22:33:44:55")/IP(dst="100.128.0.1")/Raw(load="X"*26)
    packet_4:Ether(dst="00:11:22:33:44:55")/IP(dst="100.192.0.1")/Raw(load="X"*26)

   Verify packet_1 was received by tester_port_0 and src_mac="a0:a1:a2:a3:a4:a5" dst_mac="00:01:02:03:04:05".
   Verify packet_2 was received by tester_port_1 and src_mac="b0:b1:b2:b3:b4:b5" dst_mac="10:11:12:13:14:15".
   Verify packet_3 was received by tester_port_2 and src_mac="c0:c1:c2:c3:c4:c5" dst_mac="20:21:22:23:24:25".
   Verify packet_4 was received by tester_port_3 and src_mac="d0:d1:d2:d3:d4:d5" dst_mac="30:31:32:33:34:35".

Test Case: firewall pipeline
==============================
1. Edit examples/ip_pipeline/examples/firewall.cli,
   change pci device id of LINK0, LINK1, LINK2, LINK3 to pci device id of
   dut_port_0, dut_port_1, dut_port_2, dut_port_3.

2. Run ip_pipeline app as the following::

    ./<build_target>/examples/dpdk-ip_pipeline -c 0x3 -n 4 –- -s examples/firewall.cli

3. Send following packets with one test port::

    packet_1:Ether(dst="00:11:22:33:44:55")/IP(dst="100.0.0.1")/TCP(sport=100,dport=200)/Raw(load="X"*6)
    packet_2:Ether(dst="00:11:22:33:44:55")/IP(dst="100.64.0.1")/TCP(sport=100,dport=200)/Raw(load="X"*6)
    packet_3:Ether(dst="00:11:22:33:44:55")/IP(dst="100.128.0.1")/TCP(sport=100,dport=200)/Raw(load="X"*6)
    packet_4:Ether(dst="00:11:22:33:44:55")/IP(dst="100.192.0.1")/TCP(sport=100,dport=200)/Raw(load="X"*6)

   Verify packet_1 was received by tester_port_0.
   Verify packet_2 was received by tester_port_1.
   Verify packet_3 was received by tester_port_2.
   Verify packet_4 was received by tester_port_3.

Test Case: pipeline with tap
==============================
1. Edit examples/ip_pipeline/examples/tap.cli,
   change pci device id of LINK0, LINK1 to pci device id of dut_port_0, dut_port_1.

2. Run ip_pipeline app as the following::

    ./<build_target>/examples/dpdk-ip_pipeline -c 0x3 -n 4 –- -s examples/tap.cli,

3. Send packets at tester side with scapy, verify
   packets sent from tester_port_0 can be received at tester_port_1, and vice versa.

Test Case: traffic management pipeline
========================================
1. Connect dut_port_0 to one port of ixia network traffic generator.

2. Edit examples/ip_pipeline/examples/traffic_manager.cli,
   change pci device id of LINK0 to pci device id of dut_port_0.

3. Run ip_pipeline app as the following::

    ./<build_target>/examples/dpdk-ip_pipeline -c 0x3 -n 4 -a 0000:81:00.0 -- -s examples/traffic_manager.cli

4. Config traffic with dst ipaddr increase from 0.0.0.0 to 15.255.0.0, total 4096 streams,
   also config flow tracked-by dst ipaddr, verify each flow's throughput is about linerate/4096.

Test Case: RSS pipeline
=========================
1. Edit examples/ip_pipeline/examples/rss.cli,
   change pci device id of LINK0, LINK1, LINK2, LINK3 to pci device id of
   dut_port_0, dut_port_1, dut_port_2, dut_port_3.

2. Run ip_pipeline app as the following::

    ./<build_target>/examples/dpdk-ip_pipeline -c 0x1f -n 4 –- -s examples/rss.cli

3. Send 20 IP packets randomly for one test port

4. Check the test port can be received and assigned to other ports through RSS
   Verify that the sum of packets received by all ports is 20.
   Verify all tester_port can received packets.

5. Repeat steps 3-4 to ensure that the RSS functions of all test ports are normal.
   Verify that packets of the same IP can be assigned to the same port through different test ports.

Test Case: vf l2fwd pipeline(pf bound to dpdk driver)
======================================================
1. Create vf with pf bound to dpdk driver::

    echo 1 > /sys/bus/pci/devices/0000\:05\:00.0/max_vfs
    echo 1 > /sys/bus/pci/devices/0000\:05\:00.1/max_vfs
    echo 1 > /sys/bus/pci/devices/0000\:05\:00.2/max_vfs
    echo 1 > /sys/bus/pci/devices/0000\:05\:00.3/max_vfs

   Then bind the four vfs to dpdk vfio_pci driver::

    ./usertools/dpdk-devbind.py -b vfio_pci 05:02.0 05:06.0 05:0a.0 05:0e.0

2. Start testpmd with the four pf ports::

    ./<build_target>/app/dpdk-testpmd -c 0xf0 -n 4 -a 05:00.0 -a 05:00.1 -a 05:00.2 -a 05:00.3 --file-prefix=pf --socket-mem 1024,1024 -- -i

   Set vf mac address from pf port::

    testpmd> set vf mac addr 0 0 00:11:22:33:44:55
    testpmd> set vf mac addr 1 0 00:11:22:33:44:56
    testpmd> set vf mac addr 2 0 00:11:22:33:44:57
    testpmd> set vf mac addr 3 0 00:11:22:33:44:58

3. Edit examples/ip_pipeline/examples/vf.cli,
   change pci device id of LINK0, LINK1, LINK2, LINK3 to pci device id of
   dut_vf_port_0, dut_vf_port_1, dut_vf_port_2, dut_vf_port_3.

4. Run ip_pipeline app as the following::

    ./<build_target>/examples/dpdk-ip_pipeline -c 0x3 -n 4 -a 0000:05:02.0 -a 0000:05:06.0 \
    -a 0000:05:0a.0 -a 0000:05:0e.0 --file-prefix=vf --socket-mem 1024,1024 -- -s examples/vf.cli

   The exact format of port allowlist: domain:bus:devid:func

5. Send packets at tester side with scapy::

    packet_1:Ether(dst="00:11:22:33:44:55")/IP(src="100.0.0.1",dst="100.0.0.2")/Raw(load="X"*6)
    packet_2:Ether(dst="00:11:22:33:44:56")/IP(src="100.0.0.1",dst="100.0.0.2")/Raw(load="X"*6)
    packet_3:Ether(dst="00:11:22:33:44:57")/IP(src="100.0.0.1",dst="100.0.0.2")/Raw(load="X"*6)
    packet_4:Ether(dst="00:11:22:33:44:58")/IP(src="100.0.0.1",dst="100.0.0.2")/Raw(load="X"*6)

   Verify:
   Only packet_1 sent from tester_port_0 can be received at tester_port_1,
   other packets sent from tester_port_0 cannot be received by any port.
   Only packet_2 sent from tester_port_1 can be received at tester_port_0,
   other packets sent from tester_port_1 cannot be received by any port.
   Only packet_3 sent from tester_port_2 can be received at tester_port_3,
   other packets sent from tester_port_2 cannot be received by any port.
   Only packet_4 sent from tester_port_3 can be received at tester_port_2,
   other packets sent from tester_port_3 cannot be received by any port.

Test Case: vf l2fwd pipeline(pf bound to kernel driver)
=========================================================
1. Create vf with pf bound to kernel driver::

    echo 1 > /sys/bus/pci/devices/0000\:05\:00.0/sriov_numvfs
    echo 1 > /sys/bus/pci/devices/0000\:05\:00.1/sriov_numvfs
    echo 1 > /sys/bus/pci/devices/0000\:05\:00.2/sriov_numvfs
    echo 1 > /sys/bus/pci/devices/0000\:05\:00.3/sriov_numvfs

2. Set vf mac address::

    ip link set dut_port_0 vf 0 mac 00:11:22:33:44:55
    ip link set dut_port_1 vf 0 mac 00:11:22:33:44:56
    ip link set dut_port_2 vf 0 mac 00:11:22:33:44:57
    ip link set dut_port_3 vf 0 mac 00:11:22:33:44:58

   Disable spoof checking on vfs::

    ip link set dut_port_0 vf 0 spoofchk off
    ip link set dut_port_1 vf 0 spoofchk off
    ip link set dut_port_2 vf 0 spoofchk off
    ip link set dut_port_3 vf 0 spoofchk off

   Then bind the four vfs to dpdk vfio_pci driver::

    ./usertools/dpdk-devbind.py -b vfio_pci 05:02.0 05:06.0 05:0a.0 05:0e.0

3. Edit examples/ip_pipeline/examples/vf.cli,
   change pci device id of LINK0, LINK1, LINK2, LINK3 to pci device id of
   dut_vf_port_0, dut_vf_port_1, dut_vf_port_2, dut_vf_port_3.

4. Run ip_pipeline app as the following::

    ./<build_target>/examples/dpdk-ip_pipeline -c 0x3 -n 4 -- -s examples/vf.cli

5. Send packets at tester side with scapy::

    packet_1:Ether(dst="00:11:22:33:44:55")/IP(src="100.0.0.1",dst="100.0.0.2")/Raw(load="X"*6)
    packet_2:Ether(dst="00:11:22:33:44:56")/IP(src="100.0.0.1",dst="100.0.0.2")/Raw(load="X"*6)
    packet_3:Ether(dst="00:11:22:33:44:57")/IP(src="100.0.0.1",dst="100.0.0.2")/Raw(load="X"*6)
    packet_4:Ether(dst="00:11:22:33:44:58")/IP(src="100.0.0.1",dst="100.0.0.2")/Raw(load="X"*6)

   Verify:
   Only packet_1 sent from tester_port_0 can be received at tester_port_1,
   other packets sent from tester_port_0 cannot be received by any port.
   Only packet_2 sent from tester_port_1 can be received at tester_port_0,
   other packets sent from tester_port_1 cannot be received by any port.
   Only packet_3 sent from tester_port_2 can be received at tester_port_3,
   other packets sent from tester_port_2 cannot be received by any port.
   Only packet_4 sent from tester_port_3 can be received at tester_port_2,
   other packets sent from tester_port_3 cannot be received by any port.

Test Case: crypto pipeline - AEAD algorithm in aesni_gcm
===========================================================
1. Edit examples/ip_pipeline/examples/flow_crypto.cli,
   use AEAD algorithm in aesni_gcm driver.

2. Create a cryptodev aesni_gcm::

    cryptodev CRYPTO0 dev crypto_aesni_gcm0 queue 1 1024

3. Use AEAD algorithm aes-gcm to encrypt and decrypt payload
   with specified aead_key, aead_iv, aead_aad and digest_size::

    pipeline PIPELINE0 table 0 rule add match hash ipv4_addr 100.0.0.10 action fwd port 0 sym_crypto encrypt type aead aead_algo aes-gcm aead_key 000102030405060708090a0b0c0d0e0f aead_iv 000102030405060708090a0b aead_aad 000102030405060708090a0b0c0d0e0f digest_size 8 data_offset 290

    pipeline PIPELINE0 table 0 rule add match hash ipv4_addr 100.0.0.10 action fwd port 0 sym_crypto decrypt type aead aead_algo aes-gcm aead_key 000102030405060708090a0b0c0d0e0f aead_iv 000102030405060708090a0b aead_aad 000102030405060708090a0b0c0d0e0f digest_size 8 data_offset 290

   AEAD_KEY: 16 BYTES, AEAD_IV: 12 BYTES, AAD: MAXIMUM 16 BYTES, DIGEST 8/12/16 bytes,
   You may find all supported key/aad/iv info in
   dpdk/drivers/crypto/aesni_gcm/aesni_gcm_pmd_ops.c aesni_gcm_pmd_capabilities

4. Run ip_pipeline app as the following::

    ./<build_target>/examples/dpdk-ip_pipeline -a 0000:81:00.0 --vdev crypto_aesni_gcm0
    --socket-mem 0,2048 -l 23,24,25 -- -s ./examples/ip_pipeline/examples/flow_crypto.cli

5. Send packets with IXIA port,
   Use a tool to caculate the ciphertext from plaintext and key as an expected value.
   Then compare the received ciphertext through the ip_pipeline to the expected value to see whether consistent.

   For instance, send a packet with ixia, set the frame size to 70 bytes, which is 32-byte data ipv4 pkts.
   You may add longer length, but the received packets length = ROUND_UP_MULTIPLE_TIMES_OF_16(x(size of pkt) – 38) + DIGEST_SIZE
   Track the packets of IXIA, expect receiving a packet with 78 bytes long,
   with the 32-byte payload matching encryption result of the tool, and 8 bytes digest matching the tool-computed tag.

   Set the input packet to 78 bytes in decrypt procedure,
   including the 32-byte ciphertext and 8-byte authentication tag.
   The output data is plaintext consistent with the input data of encrypt procedure.

Test Case: crypto pipeline - cipher algorithm in aesni_mb
============================================================
1. Edit examples/ip_pipeline/examples/flow_crypto.cli,
   use cipher algorithm in aesni_mb driver.

2. Create a cryptodev aesni_mb::

    cryptodev CRYPTO0 dev crypto_aesni_mb0 queue 1 1024

3. Then use cipher algorithm aes-cbc or aes-ctr to encrypt and decrypt payload
   with specified cipher_key and cipher_iv::

    pipeline PIPELINE0 table 0 rule add match hash ipv4_addr 100.0.0.10 action fwd port 0 sym_crypto encrypt type cipher cipher_algo aes-cbc cipher_key 000102030405060708090a0b0c0d0e0f cipher_iv 000102030405060708090a0b0c0d0e0f data_offset 290

    pipeline PIPELINE0 table 0 rule add match hash ipv4_addr 100.0.0.10 action fwd port 0 sym_crypto decrypt type cipher cipher_algo aes-cbc cipher_key 000102030405060708090a0b0c0d0e0f cipher_iv 000102030405060708090a0b0c0d0e0f data_offset 290

4. Run ip_pipeline app as the following::

    ./<build_target>/examples/dpdk-ip_pipeline -a 0000:81:00.0 --vdev crypto_aesni_mb0 --socket-mem 0,2048 -l 23,24,25 -- -s ./examples/ip_pipeline/examples/flow_crypto.cli

5. Send packets with IXIA port,
   Use a tool to caculate the ciphertext from plaintext and key as an expected value.
   Compare the received ciphertext through the ip_pipeline to the expected value to see whether consistent.

   For instance, send a packet with ixia, set the frame size to 70 bytes, which is 32-byte data ipv4 pkts.
   You may add longer length, but the received packets length = ROUND_UP_MULTIPLE_TIMES_OF_16(x(size of pkt) – 38)
   Track the packets of IXIA, expect receiving a packet with 70 bytes long,
   with the 32-byte payload matching encryption result of the tool.

   Set the input packet to 70 bytes in decrypt procedure too,
   The output data is plaintext consistent with the input data of encrypt procedure.

Test Case: crypto pipeline - cipher_auth algorithm in aesni_mb
=================================================================
1. Edit examples/ip_pipeline/examples/flow_crypto.cli,
   use cipher_auth algorithm in aesni_mb driver.

2. Create a cryptodev aesni_mb::

    cryptodev CRYPTO0 dev crypto_aesni_mb0 queue 1 1024

3. Then use cipher_auth algorithm aes-cbc and SHA1_HMAC to encrypt and decrypt payload
   with specified cipher_key, cipher_iv, auth_key and digest_size::

    pipeline PIPELINE0 table 0 rule add match hash ipv4_addr 100.0.0.10 action fwd port 0 sym_crypto encrypt type cipher_auth cipher_algo aes-cbc cipher_key 000102030405060708090a0b0c0d0e0f cipher_iv 000102030405060708090a0b0c0d0e0f auth_algo sha1-hmac auth_key 000102030405060708090a0b0c0d0e0f digest_size 12 data_offset 290

4. Run ip_pipeline app as the following::

    ./<build_target>/examples/dpdk-ip_pipeline -a 0000:81:00.0 --vdev crypto_aesni_mb0 --socket-mem 0,2048 -l 23,24,25 -- -s ./examples/ip_pipeline/examples/flow_crypto.cli

5. Send packets with IXIA port,
   Use a tool to caculate the ciphertext from plaintext and cipher key with AES-CBC algorithm.
   Then caculate the 12-byte digest tag from ciphertext plus IP header (52 bytes)and auth_key with SHA1-HMAC algorithm.
   Compare the received ciphertext through the ip_pipeline to the expected value to see whether consistent,
   and compare the 12-byte digest tag with the tool-computed tag.

   For instance, send a packet with ixia, set the frame size to 70 bytes, which is 32-byte data ipv4 pkts.
   You may add longer length, but the received packets length = ROUND_UP_MULTIPLE_TIMES_OF_16(x(size of pkt) – 38) + DIGEST_SIZE
   Track the packets of IXIA, expect receiving a packet with 82 bytes long,
   with the 32-byte payload matching encryption result of the tool, and 12 bytes digest matching the tool-computed tag.
