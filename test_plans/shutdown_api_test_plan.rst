.. Copyright (c) <2010-2017>, Intel Corporation
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

==========================
Shutdown API Feature Tests
==========================

This tests for Shutdown API feature can be run on linux userspace. It
will check if NIC port can be stopped and restarted without exiting the
application process. Furthermore, it will check if it can reconfigure
new configurations for a port after the port is stopped, and if it is
able to restart with those new configurations. It is based on testpmd
application.

The test is performed by running the testpmd application and using a
traffic generator. Port/queue configurations can be set interactively,
and still be set at the command line when launching the application in
order to be compatible with previous test framework.

Prerequisites
-------------

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to to load the vfio driver and bind it
to the device under test::

   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id

Assume port A and B are connected to the remote ports, e.g. packet generator.
To run the testpmd application in linuxapp environment with 4 lcores,
4 channels with other default parameters in interactive mode::

    $ ./testpmd -c 0xf -n 4 -- -i

Test Case: Stop and Restart
---------------------------

1. If the testpmd application is not launched, run it as above command. Follow
   below steps to check if it works well after re-configuring all ports without
   changing any configurations.
2. Run ``start`` to start forwarding packets.
3. Check that testpmd is able to forward traffic.
4. Run ``stop`` to stop forwarding packets.
5. Run ``port stop all`` to stop all ports.
6. Check on the tester side that the ports are down using ethtool.
7. Run ``port start all`` to restart all ports.
8. Check on the tester side that the ports are up using ethtool
9. Run ``start`` again to restart the forwarding, then start packet generator to
   transmit and receive packets, and check if testpmd is able to receive and
   forward packets successfully.

Test Case: Reset RX/TX Queues
-----------------------------

1. If the testpmd application is not launched, run it as above command. Follow
   below steps to check if it works well after reconfiguring all ports without
   changing any configurations.
2. Run ``port stop all`` to stop all ports.
3. Run ``port config all rxq 2`` to change the number of receiving queues to two.
4. Run ``port config all txq 2`` to change the number of transmitting queues to two.
5. Run ``port start all`` to restart all ports.
6. Check with ``show config rxtx`` that the configuration for these parameters changed.
7. Run ``start`` again to restart the forwarding, then start packet generator to transmit
   and receive packets, and check if testpmd is able to receive and forward packets
   successfully.

Test Case: Set promiscuous mode
-------------------------------

1. If the testpmd application is not launched, run it as above command. Follow
   below steps to check if promiscuous mode setting works well after reconfiguring
   it while all ports are stopped
2. Run ``port stop all`` to stop all ports.
3. Run ``set promisc all off`` to disable promiscuous mode on all ports.
4. Run ``port start all`` to restart all ports.
5. Run ``start`` again to restart the forwarding, then start packet generator to transmit
   and receive packets, and check that testpmd is NOT able to receive and forward packets
   successfully.
6. Run ``port stop all`` to stop all ports.
7. Run ``set promisc all on`` to enable promiscuous mode on all ports.
8. Run ``port start all`` to restart all ports.
9. Run ``start`` again to restart the forwarding, then start packet generator to transmit
   and receive packets, and check that testpmd is able to receive and forward packets
   successfully.

Test Case: Reconfigure All Ports With The Same Configurations (CRC)
-------------------------------------------------------------------

1. If the testpmd application is not launched, run it as above command. Follow
   below steps to check if it works well after reconfiguring all ports without
   changing any configurations.
2. Run ``port stop all`` to stop all ports.
3. Run ``port config all crc-strip on`` to enable the CRC stripping mode.
4. Run ``port start all`` to restart all ports.
5. Check with ``show config rxtx`` that the configuration for these parameters changed.
6. Run ``start`` again to restart the forwarding, then start packet generator to
   transmit and receive packets, and check if testpmd is able to receive and
   forward packets successfully. Check that the packet received is 4 bytes
   smaller than the packet sent.

Test Case: Change Link Speed
----------------------------

1. If the testpmd application is not launched, run it as above command. Follow
   below steps to check if it works well after reconfiguring all ports without
   changing any configurations.
2. Run ``port stop all`` to stop all ports.
3. Run ``port config all speed SPEED duplex HALF/FULL`` to select the new config for the link.
4. Run ``port start all`` to restart all ports.
5. Check on the tester side that the configuration actually changed using ethtool.
6. Run ``start`` again to restart the forwarding, then start packet generator to transmit
   and receive packets, and check if testpmd is able to receive and forward packets
   successfully.
7. Repeat this process for every compatible speed depending on the NIC driver.

Test Case: Enable/Disable Jumbo Frame
-------------------------------------

1. If the testpmd application is not launched, run it as above command. Follow
   below steps to check if it works well after reconfiguring all ports without
   changing any configurations.
2. Run ``port stop all`` to stop all ports.
3. Run ``port config all max-pkt-len 2048`` to set the maximum packet length.
4. Run ``port start all`` to restart all ports.
5. Run ``start`` again to restart the forwarding, then start packet generator to transmit
   and receive packets, and check if testpmd is able to receive and forward packets
   successfully. Check this with the following packet sizes: 2047, 2048 & 2049. Only the third one should fail.

Test Case: Enable/Disable RSS
-----------------------------

1. If the testpmd application is not launched, run it as above command. Follow
   below steps to check if it works well after reconfiguring all ports without
   changing any configurations.
2. Run ``port stop all`` to stop all ports.
3. Run ``port config rss ip`` to enable RSS.
4. Run ``port start all`` to restart all ports.
5. Run ``start`` again to restart the forwarding, then start packet generator to transmit
   and receive packets, and check if testpmd is able to receive and forward packets
   successfully.

Test Case: Change the Number of rxd/txd
---------------------------------------

1. If the testpmd application is not launched, run it as above command. Follow
   below steps to check if it works well after reconfiguring all ports without
   changing any configurations.
2. Run ``port stop all`` to stop all ports.
3. Run ``port config all rxd 1024`` to change the rx descriptors.
4. Run ``port config all txd 1024`` to change the tx descriptors.
5. Run ``port start all`` to restart all ports.
6. Check with ``show config rxtx`` that the descriptors were actually changed.
7. Run ``start`` again to restart the forwarding, then start packet generator to transmit
   and receive packets, and check if testpmd is able to receive and forward packets
   successfully.

Test Case: link stats
---------------------

1. If the testpmd application is not launched, run it as above command. Follow
   below steps to check if it works well after reconfiguring all ports without
   changing any configurations.
2. Run ``set fwd mac`` to set fwd type.
3. Run ``start`` to start the forwarding, then start packet generator to transmit
   and receive packets
4. Run ``set link-down port X`` to set all port link down
5. Check on the tester side that the configuration actually changed using ethtool.
6. Start packet generator to transmit and not receive packets
7. Run ``set link-up port X`` to set all port link up
8. Start packet generator to transmit and receive packets
   successfully.
