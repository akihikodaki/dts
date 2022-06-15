.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

==========================
Shutdown API Feature Tests
==========================

Description
===========
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
=============

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to load the vfio driver and bind it
to the device under test::

    modprobe vfio
    modprobe vfio-pci
    usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id

Assume port A and B are connected to the remote ports, e.g. packet generator.
To run the testpmd application in linuxapp environment with 4 lcores,
4 channels with other default parameters in interactive mode::

    $ ./app/dpdk-testpmd -c 0xf -n 4 -- -i

Test Case
=========

Test Case 1: Stop and restart
-----------------------------

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

Test Case 2: Reset RX/TX queues
-------------------------------

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

Test Case 3: Set promiscuous mode
---------------------------------

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

Test Case 4: Set allmulticast mode
----------------------------------

1. If the testpmd application is not launched, run it as above command. Follow
   below steps to check if allmulticast mode setting works well after reconfiguring
   it while all ports are stopped.
2. Run ``set promisc all off`` to disable promiscuous mode on all ports.
3. Run ``set allmulti all off`` to disable allmulticast mode on all ports.
4. Run ``start`` again to restart the forwarding.
5. Send packets with dst same to port address.
6. Check that testpmd is able to receive and forward packets successfully.
7. Send packets with unicast dst not same to port address.
8. Check that testpmd is NOT able to receive and forward packets successfully.
9. Send packets with multicast dst ``01:00:00:33:00:01`` packets.
10. Check that testpmd is NOT able to receive and forward packets successfully.
11. Run ``set allmulti all on`` to enable allmulticast mode on all ports.
12. Send packets with multicast dst ``01:00:00:33:00:01`` packets.
13. Check that testpmd is able to receive and forward packets successfully.
14. Send packets with unicast dst not same to port address.
15. Check that testpmd is NOT able to receive and forward packets successfully.
16. Run ``set promisc all on`` to enable promiscuous mode on all ports.
17. Send packets with unicast dst not same to port address.
18. Check that testpmd is able to receive and forward packets successfully.

Test Case 5: Reconfigure all ports with the same configurations (CRC)
---------------------------------------------------------------------

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

Test Case 6: Change link speed
------------------------------

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

Test Case 7: Change link speed VF
---------------------------------
This case support all the nic with driver i40e and ixgbe.

1. bind a PF to DPDK::
    ./usertools/dpdk-devbind.py -b igb_uio 1b:00.0
2. create a VF from this PF::
    echo 1 > /sys/bus/pci/devices/0000\:1b\:00.0/max_vfs
   bind a VF to DPDK::
    ./usertools/dpdk-devbind.py -b igb_uio 1b:02.0
3. launch testpmd with cmd::
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 0-3 -n 4 --file-prefix=minjq -- -i
4. Run ``port stop all`` to stop all ports.
5. Run ``port config all speed SPEED duplex HALF/FULL`` to select the new config for the link.
6. Run ``port start all`` to restart all ports.
   show port info all Check on the tester side that the VF configuration actually changed using ethtool.
7. Run ``start`` again to restart the forwarding, then start packet generator to transmit
   and receive packets, and check if testpmd is able to receive and forward packets
   successfully.
8. Repeat this process for every compatible speed depending on the NIC driver.

Test Case 8: Enable/Disable jumbo frame
---------------------------------------

1. If the testpmd application is not launched, run it as above command. Follow
   below steps to check if it works well after reconfiguring all ports without
   changing any configurations.
2. Run ``port stop all`` to stop all ports.
3. Run ``port config all max-pkt-len 2048`` to set the maximum packet length.
4. Run ``port start all`` to restart all ports.
5. Run ``start`` again to restart the forwarding, then start packet generator to transmit
   and receive packets, and check if testpmd is able to receive and forward packets
   successfully. Check this with the following packet sizes: 2047, 2048 & 2049. Only the third one should fail.

Test Case 9: Enable/Disable RSS
-------------------------------

1. If the testpmd application is not launched, run it as above command. Follow
   below steps to check if it works well after reconfiguring all ports without
   changing any configurations.
2. Run ``port stop all`` to stop all ports.
3. Run ``port config rss ip`` to enable RSS.
4. Run ``port start all`` to restart all ports.
5. Run ``start`` again to restart the forwarding, then start packet generator to transmit
   and receive packets, and check if testpmd is able to receive and forward packets
   successfully.

Test Case 10: Change the number of rxd/txd
------------------------------------------

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

Test Case 11: Change the number of rxd/txd after cycle
------------------------------------------------------

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
8. Run ``stop`` to stop the forwarding.
9. Run ``port stop all`` to stop all ports.
10. Run ``port start all`` to restart all ports.
11. Check again with ``show config rxtx`` that the descriptors were actually changed.
12. Run ``start`` again to restart the forwarding, then start packet generator to transmit
    and receive packets, and check if testpmd is able to receive and forward packets
    successfully.

Test Case 12: Change thresholds
-------------------------------

1. If the testpmd application is not launched, run it as above command. Follow
   below steps to check if it works well after reconfiguring all ports without
   changing any configurations.
2. Run ``port stop all`` to stop all ports.
3. If NIC is IXGBE_10G-X550EM_X_10G_T, IXGBE_10G-X550T, IXGBE_10G-X540T, IXGBE_10G-82599_SFP,
   Run ``port config all rxd 1024`` to change the rx descriptors,
   Run ``port config all txd 1024`` to change the tx descriptors.
4. Run ``port config all rxfreet 32`` to change the rx descriptors.
5. Run ``port config all txpt 64`` to change the tx descriptors.
6. Run ``port config all txht 64`` to change the tx descriptors.
7. If NIC is IGC-I225_LM, Run ``port config all txwt 16`` to change the tx descriptors.
   Else, Run ``port config all txwt 0`` to change the tx descriptors.
8. Run ``port start all`` to restart all ports.
9. Check with ``show config rxtx`` that the descriptors were actually changed.
10. Run ``start`` again to restart the forwarding, then start packet generator to transmit
    and receive packets, and check if testpmd is able to receive and forward packets
    successfully.

Test Case 13: Stress test
-------------------------

1. If the testpmd application is not launched, run it as above command. Follow
   below steps to check if it works well after reconfiguring all ports without
   changing any configurations.
2. Run ``port stop all`` to stop all ports.
3. Run ``port start all`` to restart all ports.
4. Check with ``show config rxtx`` that the descriptors were actually changed.
5. Run ``start`` again to restart the forwarding, then start packet generator to transmit
   and receive packets, and check if testpmd is able to receive and forward packets
   successfully.
6. Run ``stop`` to stop the forwarding.
7. Repeat step 2~6 for 10 times stress test.

Test Case 14: link stats
------------------------

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

Test Case 15: RX/TX descriptor status
-------------------------------------

1. Lauch testpmd with rx/tx queue number ``--txq=16 --rxq=16`` and rx/tx descriptor size ``--txd=4096 --rxd=4096``
2. Run ``show port 0 rxq * desc * status`` to check rx descriptor status.
3. Check rx descriptor status can be ``AVAILABLE``, ``DONE`` or ``UNAVAILABLE``.
4. Run ``show port 0 txq * desc * status`` to check tx descriptor status.
5. Check tx descriptor status can be ``FULL``, ``DONE`` or ``UNAVAILABLE``.
