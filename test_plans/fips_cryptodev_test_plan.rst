.. Copyright (c) <2019> Intel Corporation
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
FIPS Validation Application Tests
=======================================


Description
===========

Federal Information Processing Standards (FIPS) are publicly announced standards developed by the United States federal government for use in computer systems by non-military government agencies and government contractors.

This application is used to parse and perform symmetric cryptography computation to the NIST Cryptographic Algorithm Validation Program (CAVP) test vectors.

For an algorithm implementation to be listed on a cryptographic module validation certificate as an Approved security function, the algorithm implementation must meet all the requirements of FIPS 140-2 and must successfully complete the cryptographic algorithm validation process.

Limitations and Supported test vectors, please see http://doc.dpdk.org/guides/sample_app_ug/fips_validation.html


Prerequisites
=============

Get the latest IPSec Multi-buffer library (nasm package is required, for Ubuntu "apt install nasm", for Fedora/RHEL "dnf install nasm")::

  git clone https://github.com/intel/intel-ipsec-mb.git

  cd intel-ipsec-mb

  git checkout d3e25eed9d010b2c24b9970828eb9b45f4795c06    (latest working commit)

  make -j 4

  make install


Get/install FIPS Object Module::

  wget https://www.openssl.org/source/openssl-fips-2.0.16.tar.gz

  cd openssl-fips-2.0.16

  make

  make install


Get/install the OpenSSL library::

  wget https://www.openssl.org/source/openssl-1.0.2o.tar.gz

  export CFLAGS='-fPIC'

  ./config shared fips

  make depend

  make


Build FIPS validation application(in DPDK examples directory)::

  make -C examples/fips_validation


Test Case Common Step
=====================

Launch fips validation application command::

  ./fips_validation [EAL options]
   -- --req-file FILE_PATH/FOLDER_PATH
   --rsp-file FILE_PATH/FOLDER_PATH
   [--cryptodev DEVICE_NAME] [--cryptodev-id ID] [--path-is-folder]

req-file: The path of the request file or folder, separated by path-is-folder option.
rsp-file: The path that the response file or folder is stored. separated by path-is-folder option.
cryptodev: The name of the target DPDK Crypto device to be validated.
cryptodev-id: The id of the target DPDK Crypto device to be validated.
path-is-folder: If presented the application expects req-file and rsp-file are folder paths.


Check test results by comparing the generated .rsp files with the reference .rsp/.fax files


Test Case 01: fips_aesni_mb_aes_test
====================================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 --vdev crypto_aesni_mb_pmd_1 -- --req-file /root/FIPS/AES/req --rsp-file /root/FIPS/AES/resp --cryptodev crypto_aesni_mb_pmd_1 --path-is-folder --cryptodev-id 0 --self-test


Test Case 02: fips_aesni_mb_3des_test
=====================================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 --vdev crypto_aesni_mb_pmd_1 -- --req-file /root/FIPS/TDES/req --rsp-file /root/FIPS/TDES/resp --cryptodev crypto_aesni_mb_pmd_1 --path-is-folder --cryptodev-id 0 --self-test


Test Case 03: fips_aesni_mb_hmac_test
=====================================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 --vdev crypto_aesni_mb_pmd_1 -- --req-file /root/FIPS/HMAC/req --rsp-file /root/FIPS/HMAC/resp --cryptodev crypto_aesni_mb_pmd_1 --path-is-folder --cryptodev-id 0 --self-test


Test Case 04: fips_aesni_mb_ccm_test
====================================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 --vdev crypto_aesni_mb_pmd_1 -- --req-file /root/FIPS/CCM/req --rsp-file /root/FIPS/CCM/resp --cryptodev crypto_aesni_mb_pmd_1 --path-is-folder --cryptodev-id 0 --self-test


Test Case 05: fips_aesni_mb_cmac_test
=====================================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 --vdev crypto_aesni_mb_pmd_1 -- --req-file /root/FIPS/CMAC/req --rsp-file /root/FIPS/CMAC/resp --cryptodev crypto_aesni_mb_pmd_1 --path-is-folder --cryptodev-id 0 --self-test


Test Case 06: fips_qat_gcm_test
===============================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 -w 0000:1a:01.0 -- --req-file /root/FIPS/GCM/req --rsp-file /root/FIPS/GCM/resp --path-is-folder --cryptodev-id 0 --self-test


Test Case 07: fips_qat_aes_test
===============================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 -w 0000:1a:01.0 -- --req-file /root/FIPS/AES/req --rsp-file /root/FIPS/AES/resp --path-is-folder --cryptodev-id 0 --self-test


Test Case 08: fips_qat_3des_test
================================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 -w 0000:1a:01.0 -- --req-file /root/FIPS/TDES/req --rsp-file /root/FIPS/TDES/resp --path-is-folder --cryptodev-id 0 --self-test


Test Case 09: fips_qat_hmac_test
================================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 -w 0000:1a:01.0 -- --req-file /root/FIPS/HMAC/req --rsp-file /root/FIPS/HMAC/resp --path-is-folder --cryptodev-id 0 --self-test


Test Case 10: fips_qat_ccm_test
===============================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 -w 0000:1a:01.0 -- --req-file /root/FIPS/CCM/req --rsp-file /root/FIPS/CCM/resp --path-is-folder --cryptodev-id 0 --self-test


Test Case 11: fips_qat_cmac_test
================================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 -w 0000:1a:01.0 -- --req-file /root/FIPS/CMAC/req --rsp-file /root/FIPS/CMAC/resp --path-is-folder --cryptodev-id 0 --self-test


Test Case 12: fips_openssl_gcm_test
===================================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 --vdev crypto_openssl_pmd_1 -- --req-file /root/FIPS/GCM/req --rsp-file /root/FIPS/GCM/resp --cryptodev crypto_openssl_pmd_1 --path-is-folder --cryptodev-id 0 --self-test


Test Case 13: fips_openssl_aes_test
===================================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 --vdev crypto_openssl_pmd_1 -- --req-file /root/FIPS/AES/req --rsp-file /root/FIPS/AES/resp --cryptodev crypto_openssl_pmd_1 --path-is-folder --cryptodev-id 0 --self-test


Test Case 14: fips_openssl_3des_test
====================================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 --vdev crypto_openssl_pmd_1 -- --req-file /root/FIPS/TDES/req --rsp-file /root/FIPS/TDES/resp --cryptodev crypto_openssl_pmd_1 --path-is-folder --cryptodev-id 0 --self-test


Test Case 15: fips_openssl_hmac_test
====================================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 --vdev crypto_openssl_pmd_1 -- --req-file /root/FIPS/HMAC/req --rsp-file /root/FIPS/HMAC/resp --cryptodev crypto_openssl_pmd_1 --path-is-folder --cryptodev-id 0 --self-test


Test Case 16: fips_openssl_ccm_test
===================================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 --vdev crypto_openssl_pmd_1 -- --req-file /root/FIPS/CCM/req --rsp-file /root/FIPS/CCM/resp --cryptodev crypto_openssl_pmd_1 --path-is-folder --cryptodev-id 0 --self-test


Test Case 17: fips_aesni_gcm_gcm_test
=====================================

Test Command::

  ./fips_validation --socket-mem 2048,0 --legacy-mem -l 9,10,66 -n 6 --vdev crypto_aesni_gcm_pmd_1 -- --req-file /root/FIPS/GCM/req --rsp-file /root/FIPS/GCM/resp --cryptodev crypto_aesni_gcm_pmd_1 --path-is-folder --cryptodev-id 0 --self-test


Test Case 18: fips_self-test
============================

Test Command::

  ./fips_validation -w 0000:1a:01.0 --socket-mem 2048,0 --vdev crypto_aesni_mb_pmd_1 -- --req-file /root/FIPS/AES/req --rsp-file ./root/FIPS/AES/resp --cryptodev crypto_aesni_mb_pmd_1 --path-is-folder --self-test


Test Case 19: fips_broken-test
==============================

Test Command::

  ./fips_validation -w 0000:1a:01.0--socket-mem 2048,0 --vdev crypto_aesni_mb_pmd_1 -- --req-file /root/FIPS/AES/req --rsp-file ./root/FIPS/AES/resp --cryptodev crypto_aesni_mb_pmd_1 --path-is-folder --self-test --broken-test-id 15 --broken-test-dir dec

