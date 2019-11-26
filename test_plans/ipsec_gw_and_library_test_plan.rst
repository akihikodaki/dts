.. Copyright (c) <2019>, Intel Corporation
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
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
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

==============================================
IPSec gateway and library test plan
==============================================


Description
===========

This document provides the plan for DPDK IPSec library and gateway sample. DPDK IPsec could leverage CryptoDev API
provides the ability to do encryption/decryption by QAT or AESNI instruction set.

The testing should be tested under either Intel QuickAssist Technology
hardware accelerator or AES-NI library.

AES-NI algorithm table:

The table below contains AES-NI Algorithms with CryptoDev API.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm | Mode              | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| AES       | CBC               | Encrypt/Decrypt;Key size: 128, 256 bits                                   |
+-----------+-------------------+---------------------------------------------------------------------------+
| AES       | CTR               | Encrypt/Decrypt;Key size: 128 bits                                        |
+-----------+-------------------+---------------------------------------------------------------------------+
| SHA       |                   | SHA-1                                                                     |
+-----------+-------------------+---------------------------------------------------------------------------+
| HMAC      |                   | Support SHA implementations SHA-1;                                        |
|           |                   |                                                                           |
|           |                   | Key Size versus Block size support: Key Size must be <= block size;       |
|           |                   |                                                                           |
|           |                   | Mac Len Supported SHA-1 10, 12, 16, 20 bytes;                             |
+-----------+-------------------+---------------------------------------------------------------------------+
| 3DES      |  CBC              | Encrypt/Decrypt; Key size: 128 bits                                       |
+-----------+-------------------+---------------------------------------------------------------------------+


QAT algorithm table:

The table below contains Cryptographic Algorithm Validation with CryptoDev API.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm | Mode              | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| AES       | CBC               | Encrypt/Decrypt;Key size: 128, 256 bits                                   |
+-----------+-------------------+---------------------------------------------------------------------------+
| AES       | CTR               | Encrypt/Decrypt;Key size: 128 bits                                        |
+-----------+-------------------+---------------------------------------------------------------------------+
| AES       | GCM               | Key Sizes:128, 192 bits;                                                  |
+-----------+-------------------+---------------------------------------------------------------------------+
| SHA       |                   | SHA-1                                                                     |
+-----------+-------------------+---------------------------------------------------------------------------+
| HMAC      |                   | Support SHA implementations SHA-1;                                        |
|           |                   |                                                                           |
|           |                   | Key Size versus Block size support: Key Size must be <= block size;       |
|           |                   |                                                                           |
|           |                   | Mac Len Supported SHA-1 10, 12, 16, 20 bytes;                             |
|           |                   |                                                                           |
+-----------+-------------------+---------------------------------------------------------------------------+
| 3DES      |  CBC              | Encrypt/Decrypt; Key size: 128 bits                                       |
+-----------+-------------------+---------------------------------------------------------------------------+
| NULL      |                   | Encrypt/Decrypt; Key size: 0 b                                            |
+-----------+-------------------+---------------------------------------------------------------------------+

AES-GCM algorithm table:

The table below contains AES-GCM Algorithms with CryptoDev API.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm | Mode              | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| AES       | GCM               | Encrypt/Decrypt;Key size: 128 bits                                        |
+-----------+-------------------+---------------------------------------------------------------------------+

Prerequisites
=============

To test IPsec, an example ipsec-secgw is added into DPDK.

The test commands of ipsec-secgw is below::

    ./build/ipsec-secgw [EAL options] --
        -p PORTMASK -P -u PORTMASK -j FRAMESIZE
        -l -w REPLAY_WINOW_SIZE -e -a
        --config (port,queue,lcore)[,(port,queue,lcore)]
        --single-sa SAIDX
        --rxoffload MASK
        --txoffload MASK
        -f CONFIG_FILE_PATH

compile the applications::

    make -C ./examples/ipsec-secgw

Configuration File Syntax:

    The ``-f CONFIG_FILE_PATH`` option enables the application read and
    parse the configuration file specified, and configures the application
    with a given set of SP, SA and Routing entries accordingly. The syntax of
    the configuration file will be explained in DPDK code directory
    dpdk/doc/guides/sample_app_ug/ipsec_secgw.rst.


QAT/AES-NI installation
=======================

If CryptoDev needs to use QAT to do encryption/decryption, QAT should be installed
correctly. The steps how to install QAT is described in DPDK code directory
dpdk/doc/guides/cryptodevs/qat.rst.

If CryptoDev needs to use AES-NI to do encryption/decryption, AES-NI library should be install
correctly. The steps how to use AES-NI library is described in DPDK code directory
dpdk/doc/guides/cryptodevs/aesni_mb.rst.


Test cases: IPSec Function test
==================================
Description:
The SUT and DUT are connected through at least 2 NIC ports.

One NIC port is expected to be managed by linux on both machines and will be
used as a control path.

The second NIC port (test-port) should be bound to DPDK on the SUT, and should
be managed by linux on the DUT.

The script starts ``ipsec-secgw`` with 2 NIC devices: ``test-port`` and
``tap vdev``.

It then configures the local tap interface and the remote interface and IPsec
policies in the following way:

Traffic going over the test-port in both directions has to be protected by IPsec.

Traffic going over the TAP port in both directions does not have to be protected.

Test Topology:
---------------

Two servers are connected with one cable, Tester run DPDK ipsec-secgw sample
which includes 1 hardware NIC bind and a virtual device, DUT run linux kernal ipsec stack,
This test will use linux kernal IPSec stack verify DPDK IPSec stack::

                        +----------+                 +----------+
                        |          |                 |          |
        11.11.11.1/24   |   Tester | 11.11.11.2/24   |   DUT    |
    dtap0 ------------> |          | --------------> |          |
                        |          |                 |          |
                        +----------+                 +----------+

Test case: basic functional test
---------------------------------

Cryptodev AES-NI algorithm validation matrix is showed in table below.

+-------------+-------------+-------------+-------------+-------------+-------------+
| Method      | Cipher_algo |  Cipher_op  | Cipher_key  |  Auth_algo  |   Auth_op   |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 256         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CTR     | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | 3DES_CBC    | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+

AESNI_MB device start cmd::

    ./examples/ipsec-secgw/build/ipsec-secgw --socket-mem 2048,0 --legacy-mem -w 0000:60:00.0
    --vdev=net_tap0,mac=fixed --vdev crypto_aesni_mb_pmd_1 --vdev=crypto_aesni_mb_pmd_2 -l 9,10,11 -n 6  -- -P  --config "(0,0,10),(1,0,11)"
    -u 0x1 -p 0x3 -f /root/dts/local_conf/ipsec_test.cfg

Cryptodev QAT algorithm validation matrix is showed in table below.

+-------------+-------------+-------------+-------------+-------------+-------------+
| Method      | Cipher_algo |  Cipher_op  | Cipher_key  |  Auth_algo  |   Auth_op   |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 256         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CTR     | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | 3DES_CBC    | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | NULL        | ENCRYPT     | 0           |  NULL       | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+

+-------------+-------------+-------------+-------------+
| Method      | Aead_algo   |  Aead_op    | Aead_key    |
+-------------+-------------+-------------+-------------+
| AEAD        | AES_GCM     | ENCRYPT     | 128         |
+-------------+-------------+-------------+-------------+

QAT device start cmd::

    ./examples/ipsec-secgw/build/ipsec-secgw --socket-mem 2048,0 --legacy-mem --vdev=net_tap0,mac=fixed -w 0000:60:00.0
    -w 0000:1a:01.0 -l 9,10,11 -n 6  -- -P  --config "(0,0,10),(1,0,11)" -u 0x1 -p 0x3
    -f /root/dts/local_conf/ipsec_test.cfg

AES_GCM_PMD algorithm validation matrix is showed in table below.

+-------------+-------------+-------------+-------------+
| Method      | Aead_algo   |  Aead_op    | Aead_key    |
+-------------+-------------+-------------+-------------+
| AEAD        | AES_GCM     | ENCRYPT     | 128         |
+-------------+-------------+-------------+-------------+

AESNI_GCM device start cmd::

    ./examples/ipsec-secgw/build/ipsec-secgw --socket-mem 2048,0 --legacy-mem -w 0000:60:00.0 --vdev=net_tap0,mac=fixed
    --vdev crypto_aesni_gcm_pmd_1 --vdev=crypto_aesni_gcm_pmd_2 -l 9,10,11 -n 6  -- -P  --config "(0,0,10),(1,0,11)"
    -u 0x1 -p 0x3 -f /root/dts/local_conf/ipsec_test.cfg

Steps::

    1. start ipsec-secgw sample;
    2. config tester kernal IPSec;
    3. ping from DUT
    # ping 11.11.11.1

Expected result::

    the ping command should be get response normally.

Test Case: Packet reassemble Test
---------------------------------
Description::

    This Case is used to verify that ipsec-secgw could handle fragmented packets.

Steps::

    1. start ipsec-secgw sample;
    2. config tester kernal IPSec;
    3. ping from DUT with a packets exceeds MTU
    # ping 11.11.11.1 -s 3000
