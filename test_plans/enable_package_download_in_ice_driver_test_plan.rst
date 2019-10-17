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

==========================================================
Flexible pipeline package processing on CPK NIC mode Tests
==========================================================

Description
===========

DPDK PMD is able to load flexible pipeline package file,
process the content then program to NIC.

This is very important feature, all Classification and Qos functions
depends on this.

This feature set enabled package downloading to the device. The package is
to be in the /lib/firmware/intel/ice/ddp directory and named ice.pkg.
The package is shared by the kernel driver and the DPDK PMD.

If package download failed, driver need to go to safe mode.
RSS, QINQ, and checksum offload are disabled in safe mode.

Prerequisites
=============

Hardware::

    Ice NIC port*2
    DUT_port_0 <---> Tester_port_0
    DUT_port_1 <---> Tester_port_1

Test case 1: Download the package successfully
==============================================

1. Put the correct ice.pkg to /lib/firmware/intel/ice/ddp/ice.pkg and /lib/firmware/updates/intel/ice/ddp/ice.pkg,
   then reboot the server.

2. Start the testpmd::

    ./testpmd -c 0x3fe -n 6 -- -i --nb-cores=8 --rxq=8 --txq=8 \
    --port-topology=chained

   The testpmd can be started normally without any fail information.

3. Normal forward

   Set forward mode::

    testpmd> set mac fwd
    testpmd> start

   Send an IPV4 packet from Tester_port_0,
   Tester_port_1 can receive the forwarded packet.
   The forward can run normally.

4. The RSS function run normally.

   set rxonly mode::

    testpmd> set mac rxonly
    testpmd> start

5. Send UPD/TCP/SCTP+IPV4/IPV6 packets with packet generator
   with different IPV4/IPV6 address or TCP/UDP/SCTP ports,
   the packets can be distributed to different rx queues.

Test case 2: Driver enters Safe Mode successfully
=================================================

1. Server power on, then put a new ice.pkg to
   /lib/firmware/intel/ice/ddp/ice.pkg and /lib/firmware/updates/intel/ice/ddp/ice.pkg.
   Make sure the new ice.pkg is different with the original one.

2. Start testpmd::

    ./testpmd -c 0x3fe -n 6 \
    -w PORT0_PCI,safe-mode-support=1 -w PORT1_PCI,safe-mode-support=1 \
    -- -i --nb-cores=8 --rxq=8 --txq=8 --port-topology=chained

   There will be an error reported::

    ice_dev_init(): Failed to load the DDP package,Entering Safe Mode

   The driver need to go to safe mode.

3. Normal forward

   Set forward mode::

    testpmd> set mac fwd
    testpmd> start

   Send an IPV4 packet from Tester_port_0,
   Tester_port_1 can receive the forwarded packet.
   The forward can run normally.

4. The RSS function doesn't work.

   set rxonly mode::

    testpmd> set mac rxonly
    testpmd> start

5. Send UPD/TCP/SCTP+IPV4/IPV6 packets with packet generator
   with different IPV4/IPV6 address or TCP/UDP/SCTP ports,
   the packets can be only distributed to rx queue 0.

Test case 3: Driver enters Safe Mode failed
===========================================

1. Server power on, then put a new ice.pkg to
   /lib/firmware/intel/ice/ddp/ice.pkg and /lib/firmware/updates/intel/ice/ddp/ice.pkg.
   Make sure the new ice.pkg is different with the original one.

2. Start testpmd::

    ./testpmd -c 0x3fe -n 6 -- -i --nb-cores=8 --rxq=8 --txq=8 \
    --port-topology=chained

   There will be an error reported::

    ice_dev_init(): Failed to load the DDP package,Use safe-mode-support=1 to enter Safe Mode

   The driver failed to go to safe mode and testpmd failed to start.
