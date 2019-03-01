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
Technology) into DPDK. The QAT provides poll mode crypto driver support for
Intel® QuickAssist Adapter hardware accelerator.

The testing of CrytpoDev API should be tested under either Intel QuickAssist Technology
hardware accelerator or AES-NI library.

AESNI MB PMD algorithm table
The table below contains AESNI NI PMD algorithms which are supported in crypto l2fwd.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm | Mode              | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| AES       | CBC               |  Encrypt/Decrypt;Key size: 128, 192, 256 bits                             |
+           +-------------------+---------------------------------------------------------------------------+
|           | CTR               | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+           +-------------------+---------------------------------------------------------------------------+
|           | GCM               | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+           +-------------------+---------------------------------------------------------------------------+
|           | CCM               | Encrypt/Decrypt;Key size: 128 bits                                        |
+           +-------------------+---------------------------------------------------------------------------+
|           | XCBC              | Encrypt/Decrypt;Key size: 128 bits                                        |
+           +-------------------+---------------------------------------------------------------------------+
|           | DOCSISBPI         | Encrypt/Decrypt;Key size: 128 bits                                        |
+           +-------------------+---------------------------------------------------------------------------+
|           | CMAC              | Encrypt/Decrypt;Key size: 128 bits                                        |
+           +-------------------+---------------------------------------------------------------------------+
|           | GMAC              | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+-----------+-------------------+---------------------------------------------------------------------------+
| 3DES      | CBC               | Encrypt/Decrypt;Key size: 64, 128, 192 bits                               |
+           +-------------------+---------------------------------------------------------------------------+
|           | CTR               | Encrypt/Decrypt;Key size: 64, 128, 192 bits                               |
+-----------+-------------------+---------------------------------------------------------------------------+
| DES       | CBC               | Encrypt/Decrypt;Key size: 64 bits                                         |
+           +-------------------+---------------------------------------------------------------------------+
|           | DOCSISBPI         | Encrypt/Decrypt;Key size: 64 bits                                         |
+-----------+-------------------+---------------------------------------------------------------------------+
| md        |                   |  md5                                                                      |
+-----------+-------------------+---------------------------------------------------------------------------+
| SHA       |                   |  SHA-1, SHA-224, SHA-384, SHA-256, SHA-512                                |
+-----------+-------------------+---------------------------------------------------------------------------+
| HMAC      |                   |  Support SHA implementations SHA-1, SHA-224, SHA-256, SHA-384, SHA-512;   |
|           |                   |                                                                           |
|           |                   |  Key Size versus Block size support: Key Size must be <= block size;      |
|           |                   |                                                                           |
|           |                   |  Mac Len Supported SHA-1 10, 12, 16, 20 bytes;                            |
|           |                   |                                                                           |
|           |                   |  Mac Len Supported SHA-256 16, 24, 32 bytes;                              |
|           |                   |                                                                           |
|           |                   |  Mac Len Supported SHA-384 24,32, 40, 48 bytes;                           |
|           |                   |                                                                           |
|           |                   |  Mac Len Supported SHA-512 32, 40, 48, 56, 64 bytes;                      |
+-----------+-------------------+---------------------------------------------------------------------------+

QAT PMD algorithm table
The table below contains QAT PMD algorithms which are supported in crypto l2fwd.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm | Mode              | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| AES       | CBC               | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+           +-------------------+---------------------------------------------------------------------------+
|           | CTR               | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+           +-------------------+---------------------------------------------------------------------------+
|           | GCM               | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+           +-------------------+---------------------------------------------------------------------------+
|           | CCM               | Encrypt/Decrypt;Key size: 128 bits                                        |
+           +-------------------+---------------------------------------------------------------------------+
|           | XCBC              | Encrypt/Decrypt;Key size: 128 bits                                        |
+           +-------------------+---------------------------------------------------------------------------+
|           | DOCSISBPI         | Encrypt/Decrypt;Key size: 128 bits                                        |
+           +-------------------+---------------------------------------------------------------------------+
|           | CMAC              | Encrypt/Decrypt;Key size: 128 bits                                        |
+           +-------------------+---------------------------------------------------------------------------+
|           | GMAC              | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+-----------+-------------------+---------------------------------------------------------------------------+
| 3DES      | CBC               | Encrypt/Decrypt;Key size: 64, 128, 192 bits                               |
+           +-------------------+---------------------------------------------------------------------------+
|           | CTR               | Encrypt/Decrypt;Key size: 64, 128, 192 bits                               |
+-----------+-------------------+---------------------------------------------------------------------------+
| DES       | CBC               | Encrypt/Decrypt;Key size: 64 bits                                         |
+           +-------------------+---------------------------------------------------------------------------+
|           | DOCSISBPI         | Encrypt/Decrypt;Key size: 64 bits                                         |
+-----------+-------------------+---------------------------------------------------------------------------+
| md        |                   | md5                                                                       |
+-----------+-------------------+---------------------------------------------------------------------------+
| SHA       |                   | SHA-1, SHA-224, SHA-256, SHA-512                                          |
+-----------+-------------------+---------------------------------------------------------------------------+
| HMAC      |                   | Support SHA implementations SHA-1, SHA-224, SHA-256, SHA-512;             |
|           |                   |                                                                           |
|           |                   | Key Size versus Block size support: Key Size must be <= block size;       |
|           |                   |                                                                           |
|           |                   | Mac Len Supported SHA-1 10, 12, 16, 20 bytes;                             |
|           |                   |                                                                           |
|           |                   | Mac Len Supported SHA-224 14,16,20,24,28 bytes;                           |
|           |                   |                                                                           |
|           |                   | Mac Len Supported SHA-256 16, 24, 32 bytes;                               |
|           |                   |                                                                           |
|           |                   | Mac Len Supported SHA-384 24,32, 40, 48 bytes;                            |
|           |                   |                                                                           |
|           |                   | Mac Len Supported SHA-512 32, 40, 48, 56, 64 bytes;                       |
+-----------+-------------------+---------------------------------------------------------------------------+
| GCM       |                   | Key Sizes:128, 192, 256 bits;                                             |
+-----------+-------------------+---------------------------------------------------------------------------+
| Snow3G    |  UEA2             |  Encrypt/Decrypt; Key size: 128                                           |
+           +-------------------+---------------------------------------------------------------------------+
|           |  UIA2             |  Encrypt/Decrypt; Key size: 128                                           |
+-----------+-------------------+---------------------------------------------------------------------------+
| KASUMI    |  F8               |  Encrypt/Decrypt; Key size: 128                                           |
+           +-------------------+---------------------------------------------------------------------------+
|           |  F9               |  Encrypt/Decrypt; Key size: 128                                           |
+-----------+-------------------+---------------------------------------------------------------------------+
| ZUC       |  EEA3             |  Encrypt/Decrypt; Key size: 128                                           |
+           +-------------------+---------------------------------------------------------------------------+
|           |  EIA3             |  Encrypt/Decrypt; Key size: 128                                           |
+-----------+-------------------+---------------------------------------------------------------------------+

OPENSSL PMD algorithm table
The table below contains OPENSSL PMD algorithms which are supported in crypto l2fwd.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm | Mode              | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| AES       | CBC               |  Encrypt/Decrypt;Key size: 128, 192, 256 bits                             |
+           +-------------------+---------------------------------------------------------------------------+
|           | CTR               | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+           +-------------------+---------------------------------------------------------------------------+
|           | GCM               | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+           +-------------------+---------------------------------------------------------------------------+
|           | CCM               | Encrypt/Decrypt;Key size: 128 bits                                        |
+           +-------------------+---------------------------------------------------------------------------+
|           | XCBC              | Encrypt/Decrypt;Key size: 128 bits                                        |
+           +-------------------+---------------------------------------------------------------------------+
|           | DOCSISBPI         | Encrypt/Decrypt;Key size: 128 bits                                        |
+           +-------------------+---------------------------------------------------------------------------+
|           | GMAC              | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+-----------+-------------------+---------------------------------------------------------------------------+
| 3DES      | CBC               | Encrypt/Decrypt;Key size: 64, 128, 192 bits                               |
+           +-------------------+---------------------------------------------------------------------------+
|           | CTR               | Encrypt/Decrypt;Key size: 64, 128, 192 bits                               |
+-----------+-------------------+---------------------------------------------------------------------------+
| DES       | CBC               | Encrypt/Decrypt;Key size: 64 bits                                         |
+           +-------------------+---------------------------------------------------------------------------+
|           | DOCSISBPI         | Encrypt/Decrypt;Key size: 64 bits                                         |
+-----------+-------------------+---------------------------------------------------------------------------+
| md        |                   |  md5                                                                      |
+-----------+-------------------+---------------------------------------------------------------------------+
| SHA       |                   |  SHA-1, SHA-224, SHA-384, SHA-256, SHA-512                                |
+-----------+-------------------+---------------------------------------------------------------------------+
| HMAC      |                   |  Support SHA implementations SHA-1, SHA-224, SHA-256, SHA-384, SHA-512;   |
|           |                   |                                                                           |
|           |                   |  Key Size versus Block size support: Key Size must be <= block size;      |
|           |                   |                                                                           |
|           |                   |  Mac Len Supported SHA-1 10, 12, 16, 20 bytes;                            |
|           |                   |                                                                           |
|           |                   |  Mac Len Supported SHA-256 16, 24, 32 bytes;                              |
|           |                   |                                                                           |
|           |                   |  Mac Len Supported SHA-384 24,32, 40, 48 bytes;                           |
|           |                   |                                                                           |
|           |                   |  Mac Len Supported SHA-512 32, 40, 48, 56, 64 bytes;                      |
+-----------+-------------------+---------------------------------------------------------------------------+

AESNI GCM PMD algorithm table
The table below contains AESNI GCM PMD algorithms which are supported in crypto l2fwd.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm |  Mode             | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| AES       |  GCM              | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+           +-------------------+---------------------------------------------------------------------------+
|           |  GMAC             | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+-----------+-------------------+---------------------------------------------------------------------------+

SNOW3G PMD algorithm table
The table below contains SNOW3G PMD algorithms which are supported in crypto l2fwd.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm |  Mode             | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| SNOW3G    |  UIA2             | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+           +-------------------+---------------------------------------------------------------------------+
|           |  UEA2             | Encrypt/Decrypt;Key size: 128, 192, 256 bits                              |
+-----------+-------------------+---------------------------------------------------------------------------+

KASUMI PMD algorithm table
The table below contains KASUMI PMD algorithms which are supported in crypto l2fwd.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm |  Mode             | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| KASUMI    |  F8               | Encrypt/Decrypt;Key size: 128 bits                                        |
+           +-------------------+---------------------------------------------------------------------------+
|           |  F9               | Encrypt/Decrypt;Key size: 128 bits                                        |
+-----------+-------------------+---------------------------------------------------------------------------+

ZUC PMD algorithm table
The table below contains ZUC PMD algorithms which are supported in crypto l2fwd.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm |  Mode             | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| ZUC       |  EIA3             | Encrypt/Decrypt;Key size: 128 bits                                        |
+           +-------------------+---------------------------------------------------------------------------+
|           |  EEA3             | Encrypt/Decrypt;Key size: 128 bits                                        |
+-----------+-------------------+---------------------------------------------------------------------------+

NULL PMD algorithm table
The table below contains NULL PMD algorithms which are supported in crypto l2fwd.
Part of the algorithms are not supported currently.

+-----------+-------------------+---------------------------------------------------------------------------+
| Algorithm |  Mode             | Detail                                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+
| NULL      |                   | Encrypt/Decrypt;Key size: 0 bits                                          |
|           |                   |                                                                           |
|           |                   |  IV Lengths: 0 bits;                                                      |
|           |                   |                                                                           |
|           |                   |  Generate/Verify;Key Sizes:0 bits;                                        |
|           |                   |                                                                           |
|           |                   |  Associated Data Length: 1 bytes;                                         |
|           |                   |                                                                           |
|           |                   |  Payload Length: 0  bytes;                                                |
|           |                   |                                                                           |
|           |                   |  Tag Lengths: 0 bytes;                                                    |
+-----------+-------------------+---------------------------------------------------------------------------+

Prerequisites
=============

To test CryptoDev API, an example l2fwd-crypto is added into DPDK.

The test commands of l2fwd-crypto is below::

    ./build/l2fwd-crypto [EAL options] -- [-p PORTMASK] [-q NQ] [-s] [-T PERIOD] /
    [--cdev_type HW/SW/ANY] [--chain HASH_CIPHER/CIPHER_HASH/CIPHER_ONLY/HASH_ONLY/AEAD] /
    [--cipher_algo ALGO] [--cipher_op ENCRYPT/DECRYPT] [--cipher_key KEY] /
    [--cipher_key_random_size SIZE] [--cipher_iv IV] [--cipher_iv_random_size SIZE] /
    [--auth_algo ALGO] [--auth_op GENERATE/VERIFY] [--auth_key KEY] /
    [--auth_key_random_size SIZE] [--auth_iv IV] [--auth_iv_random_size SIZE] /
    [--aead_algo ALGO] [--aead_op ENCRYPT/DECRYPT] [--aead_key KEY] /
    [--aead_key_random_size SIZE] [--aead_iv] [--aead_iv_random_size SIZE] /
    [--aad AAD] [--aad_random_size SIZE] /
    [--digest size SIZE] [--sessionless] [--cryptodev_mask MASK] /
    [--mac-updating] [--no-mac-updating]


QAT/AES-NI installation
=======================

If CryptoDev needs to use QAT to do encryption/decryption, QAT should be installed
correctly. The steps how to install QAT is described in DPDK code directory
dpdk/doc/guides/cryptodevs/qat.rst.

If CryptoDev needs to use AES-NI to do encryption/decryption, AES-NI library should be install
correctly. The steps how to use AES-NI library is described in DPDK code directory
dpdk/doc/guides/cryptodevs/aesni_mb.rst.

If CryptoDev needs to use KASUMI to do encryption/decryption, KASUMI library should be install
correctly. The steps how to use KASUMI library is described in DPDK code directory
dpdk/doc/guides/cryptodevs/kasumi.rst.

If CryptoDev needs to use SNOW3G to do encryption/decryption, SNOW3G library should be install
correctly. The steps how to use SNOW3G library is described in DPDK code directory
dpdk/doc/guides/cryptodevs/snow3g.rst.

If CryptoDev needs to use ZUCto do encryption/decryption, ZUC library should be install
correctly. The steps how to use ZUClibrary is described in DPDK code directory
dpdk/doc/guides/cryptodevs/zuc.rst.

Test case: Cryptodev l2fwd test
===============================

For function test, the DUT forward UDP packets generated by scapy.

After sending single packet from Scapy, CrytpoDev function encrypt/decrypt the
payload in packet by using algorithm setting in command. The l2fwd-crypto
forward the packet back to tester.
Use TCPDump to capture the received packet on tester. Then tester parses the payload
and compare the payload with correct answer pre-stored in scripts::

    +----------+                 +----------+
    |          |                 |          |
    |          | --------------> |          |
    |  Tester  |                 |   DUT    |
    |          |                 |          |
    |          | <-------------> |          |
    +----------+                 +----------+

compile the applications::

    make -C ./examples/l2fwd-crypto


Sub-case: AES-NI test case
--------------------------

Cryptodev AES-NI algorithm validation matrix is showed in table below.

+-------------+-------------+-------------+-------------+-------------+-------------+
| Method      | Cipher_algo |  Cipher_op  | Cipher_key  |  Auth_algo  |   Auth_op   |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 192         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 256         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 128         |  SHA256_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 128         |  SHA384_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 128         |  SHA512_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CTR     | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CTR     | ENCRYPT     | 128         |  SHA256_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CTR     | ENCRYPT     | 128         |  SHA384_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CTR     | ENCRYPT     | 128         |  SHA512_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | DES_CBC     | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | DES_CBC     | ENCRYPT     | 128         |  SHA256_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | 3DES_CBC    | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | 3DES_CBC    | ENCRYPT     | 128         |  SHA256_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+

example::

    ./examples/l2fwd-crypto/build/l2fwd-crypto --socket-mem 1024,0 --legacy-mem -l 6,7,8 -n 2
    --vdev crypto_aesni_mb --vdev crypto_aesni_mb -- -p 0x1 --chain CIPHER_ONLY --cdev_type SW
    --cipher_algo aes-cbc --cipher_op ENCRYPT --cipher_key 00:01:02:03:04:05:06:07:08:09:0a:0b:0c:0d:0e:0f
    --cipher_iv 00:01:02:03:04:05:06:07:08:09:0a:0b:0c:0d:0e:0f --no-mac-updating

Sub-case: QAT test case
-----------------------

Cryptodev QAT algorithm validation matrix is showed in table below.

+-------------+-------------+-------------+-------------+-------------+-------------+
| Method      | Cipher_algo |  Cipher_op  | Cipher_key  |  Auth_algo  |   Auth_op   |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 192         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 256         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 128         |  SHA256_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 128         |  SHA384_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 128         |  SHA512_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CTR     | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CTR     | ENCRYPT     | 128         |  SHA256_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CTR     | ENCRYPT     | 128         |  SHA384_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CTR     | ENCRYPT     | 128         |  SHA512_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | DES_CBC     | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | DES_CBC     | ENCRYPT     | 128         |  SHA256_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | 3DES_CBC    | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | 3DES_CBC    | ENCRYPT     | 128         |  SHA256_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+

+-------------+-------------+-------------+-------------+
| Method      | Auth_algo   |  Auth_op    | Auth_key    |
+-------------+-------------+-------------+-------------+
| HASH_ONLY   | MD5         | GENERATE    | 64          |
+-------------+-------------+-------------+-------------+
| HASH_ONLY   | MD5         | GENERATE    | 128         |
+-------------+-------------+-------------+-------------+
| HASH_ONLY   | AES-XCBC-MAC| GENERATE    | 16          |
+-------------+-------------+-------------+-------------+

+-------------+-------------+-------------+-------------+
| Method      | Aead_algo   |  Aead_op    | Aead_key    |
+-------------+-------------+-------------+-------------+
| AEAD        | AES_GCM     | ENCRYPT     | 128         |
+-------------+-------------+-------------+-------------+
| AEAD        | AES_CCM     | ENCRYPT     | 128         |
+-------------+-------------+-------------+-------------+

example::

    ./examples/l2fwd-crypto/build/l2fwd-crypto --socket-mem 1024,0 --legacy-mem -l 6,7,8 -n 2
    -- -p 0x1 --chain CIPHER_ONLY --cdev_type HW --cipher_algo aes-cbc --cipher_op ENCRYPT
    --cipher_key 00:01:02:03:04:05:06:07:08:09:0a:0b:0c:0d:0e:0f
    --cipher_iv 00:01:02:03:04:05:06:07:08:09:0a:0b:0c:0d:0e:0f --no-mac-updating

Sub-case: OPENSSL test case
---------------------------

Cryptodev OPENSSL algorithm validation matrix is showed in table below.

+-------------+-------------+-------------+-------------+-------------+-------------+
| Method      | Cipher_algo |  Cipher_op  | Cipher_key  |  Auth_algo  |   Auth_op   |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 192         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 256         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 128         |  SHA256_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 128         |  SHA384_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CBC     | ENCRYPT     | 128         |  SHA512_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CTR     | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CTR     | ENCRYPT     | 128         |  SHA256_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CTR     | ENCRYPT     | 128         |  SHA384_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_CTR     | ENCRYPT     | 128         |  SHA512_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | DES_CBC     | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | DES_CBC     | ENCRYPT     | 128         |  SHA256_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | 3DES_CBC    | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | 3DES_CBC    | ENCRYPT     | 128         |  SHA256_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+

example::

    ./examples/l2fwd-crypto/build/l2fwd-crypto --socket-mem 1024,0 --legacy-mem -l 6,7,8 -n 2
    --vdev crypto_openssl_pmd --vdev crypto_openssl_pmd -- -p 0x1 --chain CIPHER_ONLY
    --cdev_type SW --cipher_algo aes-cbc --cipher_op ENCRYPT
    --cipher_key 00:01:02:03:04:05:06:07:08:09:0a:0b:0c:0d:0e:0f
    --cipher_iv 00:01:02:03:04:05:06:07:08:09:0a:0b:0c:0d:0e:0f --no-mac-updating

Sub-case: QAT/SNOW3G Snow3G test case
-------------------------------------

Cryptodev Snow3G algorithm validation matrix is showed in table below.
Cipher only, hash-only and chaining functionality is supported for Snow3g.

+-------------+-------------+-------------+-------------+
| Method      | Cipher_algo |  Cipher_op  | Cipher_key  |
+-------------+-------------+-------------+-------------+
| CIPHER_ONLY | UEA2        | ENCRYPT     | 128         |
+-------------+-------------+-------------+-------------+

+-------------+-------------+-------------+-------------+
| Method      | Auth_algo   |  Auth_op    | Auth_key    |
+-------------+-------------+-------------+-------------+
| HASH_ONLY   | UIA2        | GENERATE    | 128         |
+-------------+-------------+-------------+-------------+

example::

    ./examples/l2fwd-crypto/build/l2fwd-crypto --socket-mem 1024,0 --legacy-mem -l 6,7,8 -n 2
    -- -p 0x1 --chain HASH_ONLY --cdev_type HW --auth_algo snow3g-uia2 --auth_op GENERATE
    --auth_key 00:01:02:03:04:05:06:07:08:09:0a:0b:0c:0d:0e:0f
    --auth_iv 00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00 --digest 4 --no-mac-updating

Sub-case: QAT/KASUMI Kasumi test case
-------------------------------------

Cryptodev Kasumi algorithm validation matrix is showed in table below.
Cipher only, hash-only and chaining functionality is supported for Kasumi.

+-------------+-------------+-------------+-------------+
| Method      | Cipher_algo |  Cipher_op  | Cipher_key  |
+-------------+-------------+-------------+-------------+
| CIPHER_ONLY | F8          | ENCRYPT     | 128         |
+-------------+-------------+-------------+-------------+

+-------------+-------------+-------------+-------------+
| Method      | Auth_algo   |  Auth_op    | Auth_key    |
+-------------+-------------+-------------+-------------+
| HASH_ONLY   | F9          | GENERATE    | 128         |
+-------------+-------------+-------------+-------------+

example::

    ./examples/l2fwd-crypto/build/l2fwd-crypto --socket-mem 1024,0 --legacy-mem -l 6,7,8 -n 2
    --vdev crypto_kasumi_pmd --vdev crypto_kasumi_pmd -- -p 0x1 --chain HASH_ONLY --cdev_type SW
    --auth_algo kasumi-f9 --auth_op GENERATE
    --auth_key 00:01:02:03:04:05:06:07:08:09:0a:0b:0c:0d:0e:0f --digest 4 --no-mac-updating

Sub-case: QAT/ZUC Zuc test case
-------------------------------

Cryptodev ZUC algorithm validation matrix is showed in table below.
Cipher only, hash-only and chaining functionality is supported for ZUC.

+-------------+-------------+-------------+-------------+
| Method      | Cipher_algo |  Cipher_op  | Cipher_key  |
+-------------+-------------+-------------+-------------+
| CIPHER_ONLY | EEA2        | ENCRYPT     | 128         |
+-------------+-------------+-------------+-------------+

+-------------+-------------+-------------+-------------+
| Method      | Auth_algo   |  Auth_op    | Auth_key    |
+-------------+-------------+-------------+-------------+
| HASH_ONLY   | EIA3        | GENERATE    | 128         |
+-------------+-------------+-------------+-------------+

example::

    ./examples/l2fwd-crypto/build/l2fwd-crypto --socket-mem 1024,0 --legacy-mem -l 6,7,8 -n 2
    --vdev crypto_zuc_pmd --vdev crypto_zuc_pmd -- -p 0x1 --chain HASH_ONLY --cdev_type SW
    --auth_algo zuc-eia3 --auth_op GENERATE --auth_key 00:01:02:03:04:05:06:07:08:09:0a:0b:0c:0d:0e:0f
    --auth_iv 00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00 --digest 4 --no-mac-updating

Sub-case: AESNI-GCM test case
-----------------------------

Cryptodev AESNI-GCM algorithm validation matrix is showed in table below.

+-------------+-------------+-------------+-------------+
| Method      | Aead_algo   |  Aead_op    | Aead_key    |
+-------------+-------------+-------------+-------------+
| AEAD        | AES_GCM     | ENCRYPT     | 128         |
+-------------+-------------+-------------+-------------+

+-------------+-------------+-------------+-------------+-------------+-------------+
| Method      | Cipher_algo |  Cipher_op  | Cipher_key  |  Auth_algo  |   Auth_op   |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES_GCM     | ENCRYPT     | 128         |  AES-GCM    | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES-GMAC    | ENCRYPT     | 128         |  SHA1_HMAC  | GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+
| CIPHER_HASH | AES-GMAC    | ENCRYPT     | 128         |  SHA256_HMAC| GENERATE    |
+-------------+-------------+-------------+-------------+-------------+-------------+

example::

    ./examples/l2fwd-crypto/build/l2fwd-crypto --socket-mem 1024,0 --legacy-mem -l 6,7,8 -n 2
    --vdev crypto_aesni_gcm_pmd --vdev crypto_aesni_gcm_pmd -- -p 0x1 --chain AEAD --cdev_type SW
    --aead_algo aes-gcm --aead_op ENCRYPT --aead_key 00:01:02:03:04:05:06:07:08:09:0a:0b:0c:0d:0e:0f
    --aead_iv 00:01:02:03:04:05:06:07:08:09:0a:0b --aad 00:01:02:03:04:05:06:07:08:09:0a:0b:0c:0d:0e:0f
    --digest 16 --no-mac-updating

Sub-case: QAT/NULL null test case
---------------------------------

Cryptodev NULL algorithm validation matrix is showed in table below.
Cipher only, hash-only and chaining functionality is supported for NULL.

+-------------+-------------+-------------+-------------+
| Method      | Cipher_algo |  Cipher_op  | Cipher_key  |
+-------------+-------------+-------------+-------------+
| CIPHER_ONLY | NULL        | ENCRYPT     | 0           |
+-------------+-------------+-------------+-------------+

+-------------+-------------+-------------+-------------+
| Method      | Auth_algo   |  Auth_op    | Auth_key    |
+-------------+-------------+-------------+-------------+
| HASH_ONLY   | NULL        | GENERATE    | 0           |
+-------------+-------------+-------------+-------------+

example::

    ./examples/l2fwd-crypto/build/l2fwd-crypto --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6
    --vdev crypto_null_pmd --vdev crypto_null_pmd  --  -p 0x1 --chain CIPHER_ONLY --cdev_type SW
    --cipher_algo null --cipher_op ENCRYPT --no-mac-updating
