.. Copyright (c) <2016-2017> Intel Corporation
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

=======================================
Cryptodev Performance Application Tests
=======================================


Description
===========

This document provides the test plan for testing Cryptodev performance by
crypto perf application. The crypto perf application is a DPDK app under
DPDK app folder.

Crypto perf application supports most of Cryptodev PMDs (polling mode driver)
Intel QuickAssist Technology DH895xxC/DH_C62xx hardware
accelerator (QAT PMD), AESNI MB PMD, AESNI GCM PMD, KASUMI PMD,
SNOW3G PMD or ZUC PMD.

AESNI MB PMD algorithm table
The table below contains AESNI MB algorithms which supported in crypto perf.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm |  Mode             | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| aes       | cbc               | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+-----------+-------------------+---------------------------------------------------------------------------+
| aes       | ctr               | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+-----------+-------------------+---------------------------------------------------------------------------+
| aes       | docsisbpi         | Encrypt/Decrypt;Key size: 128, 256 bits                                   |
+-----------+-------------------+---------------------------------------------------------------------------+
| sha       |                   | sha1, sha2-224, sha2-384, sha2-256, sha2-512                              |
+-----------+-------------------+---------------------------------------------------------------------------+
| hmac      |                   | Support md5 and sha implementations sha1, sha2-224, sha2-256,             |
|           |                   |                                                                           |
|           |                   | sha2-384, sha2-512                                                        |
|           |                   |                                                                           |
|           |                   | Key Size versus Block size support: Key Size must be <= block size;       |
|           |                   |                                                                           |
|           |                   | Mac Len Supported sha1 10, 12, 16, 20 bytes;                              |
|           |                   |                                                                           |
|           |                   | Mac Len Supported sha2-256 16, 24, 32 bytes;                              |
|           |                   |                                                                           |
|           |                   | Mac Len Supported sha2-384 24,32, 40, 48 bytes;                           |
|           |                   |                                                                           |
|           |                   | Mac Len Supported sha2-512 32, 40, 48, 56, 64 bytes;                      |
+-----------+-------------------+---------------------------------------------------------------------------+

QAT algorithm table:
The table below contains QAT Algorithms which supported in crypto perf.
Part of the algorithms are not supported currently.

+---------+-------------------+---------------------------------------------------------------------------+
|Algorithm|  Mode             | Detail                                                                    |
+---------+-------------------+---------------------------------------------------------------------------+
| aes     | cbc               |  Encrypt/Decrypt;Key size: 128, 192, 256 bits                             |
+---------+-------------------+---------------------------------------------------------------------------+
| aes     | ctr               |  Encrypt/Decrypt;Key size: 128, 192, 256 bits                             |
+---------+-------------------+---------------------------------------------------------------------------+
| aes     | docsisbpi         |  Encrypt/Decrypt;Key size: 128, 256 bits                                  |
+---------+-------------------+---------------------------------------------------------------------------+
| 3des    | cbc               |  Encrypt/Decrypt;Key size: 128, 192 bits                                  |
+---------+-------------------+---------------------------------------------------------------------------+
| 3des    | ctr               |  Encrypt/Decrypt;Key size: 128, 192 bits                                  |
+---------+-------------------+---------------------------------------------------------------------------+
| sha     |                   |  sha1, sha2-224, sha2-256, sha2-384, sha2-512                             |
+---------+-------------------+---------------------------------------------------------------------------+
| hmac    |                   |  Support md5 and sha implementations sha1, sha2-224, sha2-256,            |
|         |                   |                                                                           |
|         |                   |  sha2-384, sha2-512                                                       |
|         |                   |                                                                           |
|         |                   |  Key Size versus Block size support: Key Size must be <= block size;      |
|         |                   |                                                                           |
|         |                   |  Mac Len Supported sha1 10, 12, 16, 20 bytes;                             |
|         |                   |                                                                           |
|         |                   |  Mac Len Supported sha2-256 16, 24, 32 bytes;                             |
|         |                   |                                                                           |
|         |                   |  Mac Len Supported sha2-384 24,32, 40, 48 bytes;                          |
|         |                   |                                                                           |
|         |                   |  Mac Len Supported sha2-512 32, 40, 48, 56, 64 bytes;                     |
+---------+-------------------+---------------------------------------------------------------------------+
| aes     |  gcm              |  Key Sizes:128, 192, 256 bits;                                            |
|         |                   |                                                                           |
|         |                   |  Associated Data Length: 0 ~ 240 bytes;                                   |
|         |                   |                                                                           |
|         |                   |  Payload Length: 0 ~ (2^32 -1) bytes;                                     |
|         |                   |                                                                           |
|         |                   |  IV source: external;                                                     |
|         |                   |                                                                           |
|         |                   |  IV Lengths: 96 bits;                                                     |
|         |                   |                                                                           |
|         |                   |  Tag Lengths: 8, 12, 16 bytes;                                            |
+---------+-------------------+---------------------------------------------------------------------------+
| kasumi  |  f8               |  Encrypt/Decrypt; Key size: 128                                           |
+         +-------------------+---------------------------------------------------------------------------+
|         |  f9               |  Generate/Verify; Key size: 128                                           |
+---------+-------------------+---------------------------------------------------------------------------+
| snow3g  |  uea2             |  Encrypt/Decrypt; Key size: 128                                           |
+         +-------------------+---------------------------------------------------------------------------+
|         |  uia2             |  Generate/Verify; Key size: 128                                           |
+---------+-------------------+---------------------------------------------------------------------------+

AESNI_GCM algorithm table
The table below contains AESNI GCM PMD algorithms which are supported
in crypto perf

+---------+-------------------+---------------------------------------------------------------------------+
|Algorithm|  Mode             | Detail                                                                    |
|         |                                                                                               |
+---------+-------------------+---------------------------------------------------------------------------+
| aes     |  gcm              |  Encrypt/Decrypt;Key Sizes:128, 256 bits;                                 |
|         |                   |                                                                           |
|         |                   |  IV source: external;                                                     |
|         |                   |                                                                           |
|         |                   |  IV Lengths: 96 bits;                                                     |
|         |                   |                                                                           |
|         |                   |  Generate/Verify;Key Sizes:128,192,256 bits;                              |
|         |                   |                                                                           |
|         |                   |  Associated Data Length: 0 ~ 240 bytes;                                   |
|         |                   |                                                                           |
|         |                   |  Payload Length: 0 ~ (2^32 -1) bytes;                                     |
|         |                   |                                                                           |
|         |                   |  Tag Lengths: 8, 12, 16 bytes;                                            |
+---------+-------------------+---------------------------------------------------------------------------+
| aes     | gmac              |  Generate/Verify;Key Sizes:128,192,256 bits;                              |
|         |                   |                                                                           |
|         |                   |  Associated Data Length: 0 ~ 240 bytes;                                   |
|         |                   |                                                                           |
|         |                   |  Payload Length: 0 ~ (2^32 -1) bytes;                                     |
|         |                   |                                                                           |
|         |                   |  Tag Lengths: 8, 12, 16 bytes;                                            |
+---------+-------------------+---------------------------------------------------------------------------+

OPENSSL algorithm table
The table below contains OPENSSL algorithms which are supported in crypto perf.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm |  Mode             | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| aes       | cbc               | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+-----------+-------------------+---------------------------------------------------------------------------+
| aes       | ctr               | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+-----------+-------------------+---------------------------------------------------------------------------+
| sha       |                   | sha1, sha2-224, sha2-384, sha2-256, sha2-512                              |
+-----------+-------------------+---------------------------------------------------------------------------+
| hmac      |                   | Support md5 and sha implementations sha1, sha2-224, sha2-256,             |
|           |                   |                                                                           |
|           |                   | sha2-384, sha2-512                                                        |
|           |                   |                                                                           |
|           |                   | Key Size versus Block size support: Key Size must be <= block size;       |
|           |                   |                                                                           |
|           |                   | Mac Len Supported sha1 10, 12, 16, 20 bytes;                              |
|           |                   |                                                                           |
|           |                   | Mac Len Supported sha2-256 16, 24, 32 bytes;                              |
|           |                   |                                                                           |
|           |                   | Mac Len Supported sha2-384 24,32, 40, 48 bytes;                           |
|           |                   |                                                                           |
|           |                   | Mac Len Supported sha2-512 32, 40, 48, 56, 64 bytes;                      |
+-----------+-------------------+---------------------------------------------------------------------------+

NULL algorithm table
The table below contains NULL algorithms which are supported in crypto perf.
Part of the algorithms are not supported currently.

+---------+-------------------+---------------------------------------------------------------------------+
|Algorithm|  Mode             | Detail                                                                    |
+---------+-------------------+---------------------------------------------------------------------------+
| null    |  null             |  Encrypt/Decrypt;Key Sizes:0 bits;                                        |
|         |                   |                                                                           |
|         |                   |  IV Lengths: 0 bits;                                                      |
|         |                   |                                                                           |
|         |                   |  Generate/Verify;Key Sizes:0 bits;                                        |
|         |                   |                                                                           |
|         |                   |  Associated Data Length: 1 bytes;                                         |
|         |                   |                                                                           |
|         |                   |  Payload Length: 0  bytes;                                                |
|         |                   |                                                                           |
|         |                   |  Tag Lengths: 0 bytes;                                                    |
+---------+-------------------+---------------------------------------------------------------------------+

KASUMI algorithm table
The table below contains KASUMI algorithms which are supported in crypto perf.

+---------+-------------------+---------------------------------------------------------------------------+
|Algorithm|  Mode             | Detail                                                                    |
+---------+-------------------+---------------------------------------------------------------------------+
| kasumi  |  f8               |  Encrypt/Decrypt;Key Sizes:128 bits;                                      |
|         |                   |                                                                           |
|         |                   |  IV source: external;                                                     |
|         |                   |                                                                           |
|         |                   |  IV Lengths: 64 bits;                                                     |
+---------+-------------------+---------------------------------------------------------------------------+
| kasumi  |  f9               |  Generate/Verify;Key Sizes:128  bits;                                     |
|         |                   |                                                                           |
|         |                   |  Payload Length: 64 bytes;                                                |
|         |                   |                                                                           |
|         |                   |  Tag Lengths: 4 bytes;                                                    |
+---------+-------------------+---------------------------------------------------------------------------+

SNOW3G algorithm table
The table below contains SNOW3G algorithms which are supported in crypto perf.

+---------+-------------------+---------------------------------------------------------------------------+
|Algorithm|  Mode             | Detail                                                                    |
+---------+-------------------+---------------------------------------------------------------------------+
| snow3g  |  uea2             |  Encrypt/Decrypt;Key Sizes:128 bits;                                      |
|         |                   |                                                                           |
|         |                   |  IV source: external;                                                     |
|         |                   |                                                                           |
|         |                   |  IV Lengths: 128 bits;                                                    |
+---------+-------------------+---------------------------------------------------------------------------+
| snow3g  |  uia2             |  Generate/Verify;Key Sizes:128  bits;                                     |
|         |                   |                                                                           |
|         |                   |  Payload Length: 128 bytes;                                               |
|         |                   |                                                                           |
|         |                   |  Tag Lengths: 4 bytes;                                                    |
+---------+-------------------+---------------------------------------------------------------------------+

ZUC algorithm table
The table below contains ZUC algorithms which are supported in crypto perf.

+---------+-------------------+---------------------------------------------------------------------------+
|Algorithm|  Mode             | Detail                                                                    |
+---------+-------------------+---------------------------------------------------------------------------+
| zuc     |  eea3             |  Encrypt/Decrypt;Key Sizes:128 bits;                                      |
|         |                   |                                                                           |
|         |                   |  IV source: external;                                                     |
|         |                   |                                                                           |
|         |                   |  IV Lengths: 128 bits;                                                    |
+---------+-------------------+---------------------------------------------------------------------------+
| zuc     |  eia2             |  Generate/Verify;Key Sizes:128  bits;                                     |
|         |                   |                                                                           |
|         |                   |  Payload Length: 128 bytes;                                               |
|         |                   |                                                                           |
|         |                   |  Tag Lengths: 4 bytes;                                                    |
+---------+-------------------+---------------------------------------------------------------------------+


Prerequisites
=============

To test Cryptodev performance, an application dpdk-test-crypto-perf is added into DPDK.
The test commands of dpdk-test-crypto-perf is below::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -c COREMASK --vdev (AESNI_MB|QAT|AESNI_GCM|OPENSSL|SNOW3G|KASUMI|ZUC|NULL) -a (PCI:DEVICE:FUNCTION) -a (PCI:DEVICE:FUNCTION) -- --ptest (throughput|latency) --devtype (crypto_aesni_mb|crypto_qat|crypto_aes_gcm|crypto_openssl|crypto_snow3g|crypto_kasumi|crypto_zuc|crypto_null) --optype (aead|cipher-only|auth-only|cipher-then-auth|auth-then-cipher)  --cipher-algo (ALGO) --cipher-op (encrypt|decrypt) --cipher-key-sz (key_size) --cipher-iv-sz (iv_size) --auth-algo (ALGO) --auth-op (generate|verify) --auth-key-sz (key_size) --auth-aad-sz (aad_size) --auth-digest-sz (digest_size) --total-ops (ops_number) --burst-sz (burst_size) --buffer-sz (buffer_size)

Common::

   --vdev (AESNI_MB|QAT|AESNI_GCM|OPENSSL|SNOW3G|KASUMI|ZUC|NULL) this value can be set as : crypto_aesni_mb_pmd, crypto_aes_gcm_pmd, crypto_openssl_pmd, crypto_snow3g_pmd, crypto_kasumi_pmd, crypto_zuc_pmd or  crypto_null_pmd. If pmd is QAT this parameter should not be set.

    -a (PCI:DEVICE:FUNCTION) allowlist, specify the network interfaces or/and QAT devices that will be used by test application.

    --optype (aead|cipher-only|auth-only|cipher-then-auth|auth-then-cipher): if cipher-algo is aes-gcm or gmac this value must be set to aead. Otherwise, it will be set to others. Notice, null algorithm only support cipher-only test.

    --ptest (throughput/latency/verify) set test type.

Other parameters please reference above table's parameter.

Software
--------

dpdk: http://dpdk.org/git/dpdk
multi-buffer library: https://github.com/01org/intel-ipsec-mb
Intel QuickAssist Technology Driver: https://01.org/packet-processing/intel%C2%AE-quickassist-technology-drivers-and-patches

General set up
--------------
1, Compile DPDK::

    CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc -j 110

2, Get the pci device id of QAT::

   ./dpdk/usertools/dpdk-devbind.py --status-dev crypto

3, Bind QAT VF port to dpdk::

   ./dpdk/usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:1a:01.0

Test case
=========

Test Case 01: Cryptodev Thoughput Performance Test
==================================================

QAT PMD command line::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -c 0xf -a 0000:1a:01.0 -- --ptest throughput --devtype crypto_qat --optype cipher-then-auth  --cipher-algo aes-cbc --cipher-op encrypt --cipher-key-sz 16 --cipher-iv-sz 16 --auth-algo sha1-hmac --auth-op generate --auth-key-sz 64 --auth-aad-sz 0 --auth-digest-sz 20 --total-ops 10000000 --burst-sz 32 --buffer-sz 1024

AESNI_MB PMD command line::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -c 0xf --vdev crypto_aesni_mb_pmd  -- --ptest throughput --devtype crypto_aesni_mb --optype cipher-then-auth  --cipher-algo aes-cbc --cipher-op encrypt --cipher-key-sz 16 --cipher-iv-sz 16 --auth-algo sha1-hmac --auth-op generate --auth-key-sz 64 --auth-aad-sz 0 --auth-digest-sz 20 --total-ops 10000000 --burst-sz 32 --buffer-sz 1024

AESNI_GCM PMD command line::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -c 0xf --vdev crypto_aesni_gcm_pmd  -- --ptest throughput --devtype crypto_aesni_gcm  --optype aead  --cipher-algo aes-gcm --cipher-op encrypt --cipher-key-sz 16 --cipher-iv-sz 12 --auth-algo aes-gcm --auth-op generate --auth-key-sz 16 --auth-aad-sz 4 --auth-digest-sz 12 --total-ops 10000000 --burst-sz 32 --buffer-sz 1024

KASUMI PMD command line::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -c 0xf --vdev crypto_kasumi_pmd  -- --ptest throughput --devtype crypto_kasumi --optype cipher-then-auth  --cipher-algo kasumi-f8 --cipher-op encrypt --cipher-key-sz 16 --cipher-iv-sz 8 --auth-algo kasumi-f9 --auth-op generate --auth-key-sz 16 --auth-aad-sz 8 --auth-digest-sz 4 --total-ops 10000000 --burst-sz 32 --buffer-sz 1024

SNOW3G PMD command line::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -c 0xf --vdev crypto_snow3g_pmd  -- --ptest throughput --devtype crypto_snow3g --optype cipher-then-auth  --cipher-algo snow3g-uea2 --cipher-op encrypt --cipher-key-sz 16 --cipher-iv-sz 16 --auth-algo snow3g-uia2 --auth-op generate --auth-key-sz 16 --auth-aad-sz 16 --auth-digest-sz 4 --total-ops 10000000 --burst-sz 32 --buffer-sz 1024

ZUC PMD command line::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -c 0xf --vdev crypto_zuc_pmd  -- --ptest throughput --devtype crypto_zuc_mb --optype cipher-then-auth  --cipher-algo zuc-eea3 --cipher-op encrypt --cipher-key-sz 16 --cipher-iv-sz 16 --auth-algo zuc-eia3  --auth-op generate --auth-key-sz 16 --auth-aad-sz 16 --auth-digest-sz 4 --total-ops 10000000 --burst-sz 32 --buffer-sz 1024


Test Case 02: Cryptodev Latency Performance Test
================================================

AESNI_MB PMD command line::

  ./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -l 9,10,11,12 -n 4 --vdev crypto_aesni_mb1 --vdev crypto_aesni_mb2 -a 0000:1a:01.0 -- --devtype crypto_aesni_mb --cipher-algo aes-cbc --cipher-key-sz 16 --cipher-iv-sz 16 --cipher-op encrypt --optype cipher-only --silent --ptest latency --total-ops 10

  ./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -l 9,10,11,12 -n 4 --vdev crypto_aesni_mb1 --vdev crypto_aesni_mb2 -a 0000:1a:01.0 -- --ptest latency --devtype crypto_aesni_mb --optype cipher-then-auth --cipher-algo aes-cbc --cipher-op encrypt --cipher-key-sz 16 --auth-algo sha1-hmac --auth-op generate --auth-key-sz 64 --digest-sz 12 --total-ops 10000000 --burst-sz 32 --buffer-sz 64


AESNI_GCM PMD command line::

  ./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -l 10,11 -n 4 --vdev crypto_aesni_gcm_pmd_1 -- --aead-key-sz 16 --buffer-sz 64 --optype aead --ptest latency --aead-aad-sz 16 --devtype crypto_aesni_gcm --aead-op encrypt --burst-sz 32 --total-ops 10000000 --silent  --digest-sz 16 --aead-algo aes-gcm --aead-iv-sz 12


QAT PMD command line::

  ./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -l 9,10,11,12 -n 4  -a 0000:1a:01.0  -a 0000:1a:01.1  -a 0000:1a:01.2 -- --devtype crypto_qat --cipher-algo aes-cbc --cipher-key-sz 16 --cipher-iv-sz 16 --cipher-op encrypt --optype cipher-only --silent --ptest latency --total-ops 10

	./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -l 9,10,11,12 -n 4  -a 0000:1a:01.0  -a 0000:1a:01.1  -a 0000:1a:01.2 -- --ptest latency --devtype crypto_qat --optype cipher-then-auth --cipher-algo aes-cbc --cipher-op encrypt --cipher-key-sz 16 --auth-algo sha1-hmac --auth-op generate --auth-key-sz 64 --digest-sz 12 --total-ops 10000000 --burst-sz 32 --buffer-sz 64
	
	./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -l 10,11 -n 4 -a 0000:1a:01.0 -- --aead-key-sz 16 --buffer-sz 64 --optype aead --ptest latency --aead-aad-sz 16 --devtype crypto_qat --aead-op encrypt --burst-sz 32 --total-ops 10000000 --silent  --digest-sz 16 --aead-algo aes-gcm --aead-iv-sz 12


Test Case 03: Cryptodev Verify Performance Test
===============================================

For verify operation, you need to specify a vector file by --test-file option. Please check details at http://doc.dpdk.org/guides/tools/cryptoperf.html

AESNI_MB PMD command line::

  ./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf --vdev crypto_aesni_mb_pmd_1 -l 9,10 -n 6  -- --buffer-sz 32 --optype cipher-then-auth --ptest verify --auth-key-sz 64 --cipher-key-sz 32 --devtype crypto_aesni_mb --cipher-iv-sz 16 --auth-op generate --burst-sz 32 --total-ops 10000000 --silent  --digest-sz 12 --auth-algo sha1-hmac --cipher-algo aes-cbc --cipher-op encrypt --test-name sha1_hmac_buff_32  --test-file test_aes_cbc.data

QAT PMD command line::

	./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -a 0000:1a:01.0 -l 9,10 -n 6  -- --buffer-sz 32 --optype cipher-then-auth --ptest verify --auth-key-sz 64 --cipher-key-sz 32 --devtype crypto_qat --cipher-iv-sz 16 --auth-op generate --burst-sz 32 --total-ops 30000000 --silent  --digest-sz 20 --auth-algo sha1-hmac --cipher-algo aes-cbc --cipher-op encrypt --test-name sha1_hmac_buff_32  --test-file test_aes_cbc.data

OPENSSL PMD and QAT PMD command line::
	
  ./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -l 9,10,11,12 -n 4 --vdev crypto_openssl -a 0000:1a:01.0 -- --devtype crypto_openssl --aead-algo aes-gcm --aead-key-sz 16 --aead-iv-sz 12 --aead-op encrypt --aead-aad-sz 16 --digest-sz 16 --optype aead --silent --ptest verify --burst-sz 32 --buffer-sz 32 --total-ops 10 --test-name aes_gcm_buff_32 --test-file test_aes_gcm.data

OPENSSL PMD command line::

  ./x86_64-native-linuxapp-gcc/app/dpdk-test-crypto-perf -l 9,10,11,12 -n 4 --vdev crypto_openssl -- --devtype crypto_openssl --aead-algo aes-gcm --aead-key-sz 16 --aead-iv-sz 12 --aead-op encrypt --aead-aad-sz 16 --digest-sz 16 --optype aead --silent --ptest verify --burst-sz 32 --buffer-sz 32 --total-ops 10 --test-name aes_gcm_buff_32 --test-file test_aes_gcm.data

