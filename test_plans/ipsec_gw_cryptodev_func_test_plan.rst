.. Copyright (c) <2010-2017> Intel Corporation
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

===================
CryptoDev API Tests
===================


Description
===========

This document provides the plan for testing CryptoDev API. CryptoDev API
provides the ability to do encryption/decryption by integrating QAT (Intel® QuickAssist
Technology) into DPDK.

The testing of CrytpoDev API should be tested under either Intel QuickAssist Technology
hardware accelerator or AES-NI library.

AES-NI algorithm table
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

AES-GCM algorithm table
The table below contains AES-GCM Algorithms with CryptoDev API.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm | Mode              | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| AES       | GCM               | Encrypt/Decrypt;Key size: 128 bits                                        |
+-----------+-------------------+---------------------------------------------------------------------------+

NULL algorithm table
The table below contains NULL Algorithms with CryptoDev API.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm | Mode              | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| NUL       |                   | Encrypt/Decrypt;Key size: 0 bits                                          |
+-----------+-------------------+---------------------------------------------------------------------------+

Limitations
===========

* No IPv6 options headers.
* No chained mbufs.

Prerequisites
=============

To test CryptoDev API, an example ipsec-secgw is added into DPDK.

The test commands of ipsec-secgw is below::


    ./build/ipsec-secgw [EAL options] --
        -p PORTMASK -P -u PORTMASK -j FRAMESIZE
        -l -a REPLAY_WINOW_SIZE -e -a
        --config (port,queue,lcore)[,(port,queue,lcore]
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


Test case: CryptoDev Function test
==================================

For function test, the DUT forward UDP packets generated by scapy.

After sending single packet from Scapy, CrytpoDev function encrypt/decrypt the
payload in packet by using algorithm setting in command. The ipsec-secgw the
packet back to tester.

   +----------+                 +----------+
   |          |                 |          |
   |          | --------------> |          |
   |  Tester  |                 |   DUT    |
   |          |                 |          |
   |          | <-------------> |          |
   +----------+                 +----------+

Sub-case: AES-NI test case
--------------------------

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

example::

    ./examples/ipsec-secgw/build/ipsec-secgw --socket-mem 2048,0 --legacy-mem -a 0000:60:00.0 -a 0000:60:00.2
    --vdev crypto_aesni_mb_pmd_1 --vdev=crypto_aesni_mb_pmd_2 -l 9,10,11 -n 6  -- -P  --config "(0,0,10),(1,0,11)"
    -u 0x1 -p 0x3 -f /root/dts/local_conf/ipsec_test.cfg

Sub-case: QAT test case
---------------------------

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

example::

    ./examples/ipsec-secgw/build/ipsec-secgw --socket-mem 2048,0 --legacy-mem -a 0000:60:00.0 -a 0000:60:00.2
    -a 0000:1a:01.0 -l 9,10,11 -n 6  -- -P  --config "(0,0,10),(1,0,11)" -u 0x1 -p 0x3
    -f /root/dts/local_conf/ipsec_test.cfg

Sub-case: AES-GCM test case
------------------------------

Cryptodev AES-GCM algorithm validation matrix is showed in table below.

+-------------+-------------+-------------+-------------+
| Method      | Aead_algo   |  Aead_op    | Aead_key    |
+-------------+-------------+-------------+-------------+
| AEAD        | AES_GCM     | ENCRYPT     | 128         |
+-------------+-------------+-------------+-------------+

example::

    ./examples/ipsec-secgw/build/ipsec-secgw --socket-mem 2048,0 --legacy-mem -a 0000:60:00.0 -a 0000:60:00.2
    --vdev crypto_aesni_gcm_pmd_1 --vdev=crypto_aesni_gcm_pmd_2 -l 9,10,11 -n 6  -- -P  --config "(0,0,10),(1,0,11)"
    -u 0x1 -p 0x3 -f /root/dts/local_conf/ipsec_test.cfg

Sub-case: NULL test case
------------------------------

Cryptodev NULL algorithm validation matrix is showed in table below.

+-------------+-------------+-------------+-------------+-------------+-------------+
| Method      | Cipher_algo |  Cipher_op  | Cipher_key  |  Auth_algo  |   Auth_op   |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | NULL        | ENCRYPT     | 0           |  NULL       | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+

example::

    ./examples/ipsec-secgw/build/ipsec-secgw --socket-mem 2048,0 --legacy-mem -a 0000:60:00.0 -a 0000:60:00.2
    --vdev crypto_null_pmd_1 --vdev=crypto_null_pmd_2 -l 9,10,11 -n 6  -- -P  --config "(0,0,10),(1,0,11)"
    -u 0x1 -p 0x3 -f /root/dts/local_conf/ipsec_test.cfg
