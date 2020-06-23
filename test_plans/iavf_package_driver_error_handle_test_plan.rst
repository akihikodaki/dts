.. Copyright (c) <2020>, Intel Corporation
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

===================================================
IAVF Flexible Package and driver error handle check
===================================================

Description
===========
1. The feature is to check the CVL 100G and 25G NIC, when the using old version driver and latest DDP package, 
   will cause to the RSS rule create fail, because the old version driver vers does not support RSS feature in iavf.
2. The feature is to check the CVL 100G and 25G NIC, when the using old version ddp package or invalide ddp package and latest version driver,
   wll cause to the VF start fail, because the old version package or invalid package does not support VF create for the IAVF

Prerequisites
=============
1. Hardware:
   columbiaville_25g/columbiaville_100g

2. Software:
   dpdk: http://dpdk.org/git/dpdk
   
   Copy correct ``ice.pkg`` into ``/usr/lib/firmware/intel/ice/ddp/``, \
   Prepare driver with latest version
   Prepare driver with a old special version ice-0.10.0_rc17

3. Copy specific ice package to /lib/firmware/updates/intel/ice/ddp/ice.pkg,
   then load driver::

     rmmod ice
     insmod ice.ko

4. Compile DPDK::

     make -j install T=x86_64-native-linuxapp-gcc
	 
Test Case 1: Check old driver and latest commes pkg compatibility
=================================================================
1. change to Old driver and latst comms pkgs of version
   Driver version : ice-0.10.0_rc17
   DDP pkg version: ice_comms-1.3.16.0
   
2. Generate 1 VFs on PF0 and set mac address for each VF::
    modprobe vfio-pci
    echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs
    ip link set enp177s0f0 vf 0 mac 00:11:22:33:44:55

3. Bind the pci device id of DUT in VFs::
    ./usertools/dpdk-devbind.py -b vfio-pci 0000:b1:01.0

4. Launch the testpmd
    ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -w b1:01.0 --file-prefix=vf -- -i --rxq=16 --txq=16  --nb-cores=2

5. Create a rss rule
    testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end

Expected output in ctreat result::
    The rule create should fail and with cause with below
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

Note. the rule should create fail, because the rule should does not support in old driver version.

Test Case 2: Check latst driver and invalid commes pkg compatibility
====================================================================
1. change to Latest driver and old pkgs of version
   Driver version : latst version
   DDP pkg version: ice-1.2.0.1.pkg or touch to pkg file is invalid 

2. Generate 1 VFs on PF0 and set mac address for each VF::
   modprobe vfio-pci
   echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs

Expected output in VF start result::
   echo 1 > /sys/bus/pci/devices/0000\:b1\:00.0/sriov_numvfs
   -bash: echo: write error: Operation not supported

Note. the error log is expected, because the vf does not support invalid commes pkg.
