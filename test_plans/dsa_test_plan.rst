.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2023 Intel Corporation

=============
DSA test plan
=============

Description
===========

This sample is intended as a demonstration of the basic components of a DPDK
forwarding application and example of how to use the DMAdev API to make a packet
copy application.

Also while forwarding, the MAC addresses are affected as follows:

*   The source MAC address is replaced by the TX port MAC address

*   The destination MAC address is replaced by  02:00:00:00:00:TX_PORT_ID

This application can be used to compare performance of using software packet
copy with copy done using a DMA device for different sizes of packets.
The example will print out statistics each second. The stats shows
received/send packets and packets dropped or failed to copy.

In order to run the hardware copy application, the copying device
needs to be bound to user-space IO driver.

Refer to the "DMAdev library" chapter in the "Programmers guide" for information
on using the library.

The application requires a number of command line options:

.. code-block:: console

    ./<build_dir>/examples/dpdk-dma [EAL options] -- [-p MASK] [-q NQ] [-s RS] [-c <sw|hw>]
        [--[no-]mac-updating] [-b BS] [-f FS] [-i SI]

where,

*   p MASK: A hexadecimal bitmask of the ports to configure (default is all)

*   q NQ: Number of Rx queues used per port equivalent to DMA channels
    per port (default is 1)

*   c CT: Performed packet copy type: software (sw) or hardware using
    DMA (hw) (default is hw)

*   s RS: Size of dmadev descriptor ring for hardware copy mode or rte_ring for
    software copy mode (default is 2048)

*   --[no-]mac-updating: Whether MAC address of packets should be changed
    or not (default is mac-updating)

*   b BS: set the DMA batch size

*   f FS: set the max frame size

*   i SI: set the interval, in second, between statistics prints (default is 1)

The application can be launched in various configurations depending on
provided parameters. The app can use up to 2 lcores: one of them receives
incoming traffic and makes a copy of each packet. The second lcore then
updates MAC address and sends the copy. If one lcore per port is used,
both operations are done sequentially. For each configuration an additional
lcore is needed since the main lcore does not handle traffic but is
responsible for configuration, statistics printing and safe shutdown of
all ports and devices.

The application can use a maximum of 8 ports.

To run the application in a Linux environment with 3 lcores (the main lcore,
plus two forwarding cores), a single port (port 0), software copying and MAC
updating issue the command:

    $ ./<build_dir>/examples/dpdk-dma -l 0-2 -n 2 -- -p 0x1 --mac-updating -c sw

To run the application in a Linux environment with 2 lcores (the main lcore,
plus one forwarding core), 2 ports (ports 0 and 1), hardware copying and no MAC
updating issue the command:

    $ ./<build_dir>/examples/dpdk-dma -l 0-1 -n 1 -- -p 0x3 --no-mac-updating -c hw

Prerequisites
=============

Test flow
---------
    
NIC RX -> copy packet -> free original -> update mac addresses -> NIC TX

General set up
--------------
1. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110
    For example:
    CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc -j 110

Test case
=========

Test Case 1: DMA basic test with differnet size packets using DSA dpdk driver
-----------------------------------------------------------------------------

1.Bind 1 DSA port and 1 NIC port to vfio-pci driver.

2.Launch dma app::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-1 -n 2 -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=1 -- -p 0x1 -q 1 --mac-updating -c hw

3.Send different size packets (64B, 256B, 512B, 1024B, IMIX) from TG to NIC.

4.Check performance from “Total packets Tx” and check log includes "Worker Threads = 1, Copy Mode = hw".

Test Case 2: DMA test with multi-threads using DSA dpdk driver
--------------------------------------------------------------

1.Bind 1 DSA port and 1 NIC port to vfio-pci driver.

2.Launch dma app with three cores::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-2 -n 2 -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=1 -- -p 0x1 -q 1 --mac-updating -c hw

3. Send different size packets from TG to NIC.

4.Check performance from “Total packets Tx” and check log includes "Worker Threads = 2, Copy Mode = hw".

Test Case 3: DMA test with multi NIC ports using DSA dpdk driver
----------------------------------------------------------------

1.Bind 1 DSA port and 2 NIC ports to vfio-pci driver.

2.Launch dma app with multi-ports::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-4 -n 2 -a 0000:29:00.0 -a 0000:29:00.1 -a 0000:6a:01.0,max_queues=2 -- -p 0x3 -q 1 --mac-updating -c hw

3.Send different size packets (64B, 256B, 512B, 1024B, IMIX) from TG to two NIC ports.

4.Check stats of two ports, each port's performance shows in “Total packets Tx” and each port's log includes "Worker Threads = 2, Copy Mode = hw".

Test Case 4: DMA test with multi-queues using DSA dpdk driver
-------------------------------------------------------------

1.Bind 1 DSA port and 1 NIC port to vfio-pci driver.

2.Launch dma app with multi-queues::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-2 -n 2 -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=2 -- -p 0x1 -q 2 --mac-updating -c hw

3. Send random ip packets (64B, 256B, 512B, 1024B, IMIX) from TG to NIC port.

4. Check stats of dma app, "Worker Threads = 2, Copy Mode = hw, Rx Queues = 2" and each dma channel can enqueue packets.

5. Repeat step2 to step4 with queue number 4 and qemu number 8, at the same time, set max_queues equal to queue number.
Check performance gains status when queue numbers added.

Test Case 5: DMA performance comparison between mac-updating and no-mac-updating using DSA dpdk driver
------------------------------------------------------------------------------------------------------

1.Bind 1 DSA port and 1 NIC port to vfio-pci driver.

2.Launch dma app::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-1 -n 2 -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=2 -- -p 0x1 -q 2 --no-mac-updating -c hw

3. Send random ip packets (64B, 256B, 512B, 1024B, IMIX) from TG to NIC port.

4. Check performance from dma app::

    Total packets Tx:                   xxx [pps]

5.Launch dma app::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-1 -n 2 -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=2 -- -p 0x1 -q 2 --mac-updating -c hw

6. Send random ip packets (64B, 256B, 512B, 1024B, IMIX) from TG to NIC port.

7. Check performance from dma app::

    Total packets Tx:                   xxx [pps]
  
Test Case 6: DMA performance comparison between SW copies and HW copies using DSA dpdk driver  
---------------------------------------------------------------------------------------------

1.Bind 1 DSA port and 1 NIC port to vfio-pci driver.

2.Launch dma app with SW mode::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-2 -n 2 -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=4 -- -p 0x1 -q 4 --mac-updating  -c sw

3. Send random ip packets with different packet size,includes [64, 128, 256, 512, 1024, 1518] from TG.

4. Check performance from dma app::

    Total packets Tx:                   xxx [pps]

5.Launch dma app with HW mode::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-2 -n 2 -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=4 -- -p 0x1 -q 4 --mac-updating -c hw

6. Send random ip packets with different packet size,includes [64, 128, 256, 512, 1024, 1518] from TG.

7. Check performance from dma app and compare with hw copy test::

    Total packets Tx:                   xxx [pps]

Test Case 7: DMA basic test with differnet size packets using DSA kernel driver
-------------------------------------------------------------------------------

1.Bind 1 DSA port to idxd driver and 1 NIC port to vfio-pci driver::

   <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 29:00.0

   ls /dev/dsa #check wq configure, reset if exist
   <dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
   <dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
   ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 1 0
   ls /dev/dsa #check wq configure success

2.Launch dma app::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-1 -n 2 -a 0000:29:00.0 -a wq0.0 -- -p 0x1 -q 1 --mac-updating -c hw

3.Send different size packets (64B, 256B, 512B, 1024B, IMIX) from TG to NIC.

4.Check performance from “Total packets Tx” and check log includes "Worker Threads = 1, Copy Mode = hw".

Test Case 8: DMA test with multi-threads using DSA kernel driver
----------------------------------------------------------------

1.Bind 1 DSA port to idxd driver and 1 NIC port to vfio-pci driver.

2.Launch dma app with three cores::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-2 -n 2 -a 0000:29:00.0 -a wq0.0 -- -p 0x1 -q 1 --mac-updating -c hw

3. Send different size packets from TG to NIC.

4.Check performance from “Total packets Tx” and check log includes "Worker Threads = 2, Copy Mode = hw".

Test Case 9: DMA test with multi NIC ports using DSA kernel driver
------------------------------------------------------------------

1.Bind 1 DSA port to idxd driver and two NIC ports to vfio-pci driver::

   <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 29:00.0

   ls /dev/dsa #check wq configure, reset if exist
   <dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
   <dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
   ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
   ls /dev/dsa #check wq configure success

2.Launch dma app with multi-ports::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-4 -n 2 -a 0000:29:00.0 -a 0000:29:00.1 -a wq0.0 -a wq0.1 -- -p 0x3 -q 1 --mac-updating -c hw

3.Send different size packets (64B, 256B, 512B, 1024B, IMIX) from TG to two NIC ports.

4.Check stats of two ports, each port's performance shows in “Total packets Tx” and each port's log includes "Worker Threads = 2, Copy Mode = hw".

Test Case 10: DMA test with multi-queues using DSA kernel driver
----------------------------------------------------------------

1.Bind 1 DSA port to idxd driver and 1 NIC port to vfio-pci driver::

   <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 29:00.0

   ls /dev/dsa #check wq configure, reset if exist
   <dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
   <dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
   ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
   ls /dev/dsa #check wq configure success

2.Launch dma app with multi-queues::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-2 -n 2 -a 0000:29:00.0 -a wq0.0 -a wq0.1 -- -p 0x1 -q 2 --mac-updating -c hw

3. Send random ip packets (64B, 256B, 512B, 1024B, IMIX) from TG to NIC port.

4. Check stats of dma app, "Worker Threads = 2, Copy Mode = hw, Rx Queues = 2" and each dma channel can enqueue packets.

5. Repeat step2 to step4 with queue number 4 and qemu number 8, at the same time, reset and create WQ with the same number of queue numbers.
Check performance gains status when queue numbers added.

Test Case 11: DMA performance comparison between mac-updating and no-mac-updating using DSA kernel driver
---------------------------------------------------------------------------------------------------------

1.Bind 1 DSA port to idxd driver and 1 NIC port to vfio-pci driver::

   <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 29:00.0

   ls /dev/dsa #check wq configure, reset if exist
   <dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
   <dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
   ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0
   ls /dev/dsa #check wq configure success

2.Launch dma app::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-1 -n 2 -a 0000:29:00.0 -a wq0.0 -a wq0.1 -- -p 0x1 -q 2 --no-mac-updating -c hw

3. Send random ip 64B packets from TG.

4. Check performance from dma app::

    Total packets Tx:                   xxx [pps]

5.Launch dma app::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-1 -n 2 -a 0000:29:00.0 -a wq0.0 -a wq0.1 -- -p 0x1 -q 2 --mac-updating -c hw

6. Send random ip 64B packets from TG.

7. Check performance from dma app::

    Total packets Tx:                   xxx [pps]

Test Case 12: DMA performance comparison between SW copies and HW copies using DSA kernel driver  
------------------------------------------------------------------------------------------------

1.Bind 1 DSA port to idxd driver and 1 NIC port to vfio-pci driver::

   <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 29:00.0

   ls /dev/dsa #check wq configure, reset if exist
   <dpdk dir># ./usertools/dpdk-devbind.py -u 6a:01.0
   <dpdk dir># ./usertools/dpdk-devbind.py -b idxd 6a:01.0
   ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0
   ls /dev/dsa #check wq configure success

2.Launch dma app with SW mode::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-2 -n 2 -a 0000:29:00.0 -a wq0.0 -a wq0.1 -a wq0.2 -a wq0.3 -- -p 0x1 -q 4 --mac-updating  -c sw

3. Send random ip packets with different packet size,includes [64, 128, 256, 512, 1024, 1518] from TG.

4. Check performance from dma app::

    Total packets Tx:                   xxx [pps]

5.Launch dma app with HW mode::

   ./x86_64-native-linuxapp-gcc/examples/dpdk-dma -l 0-2 -n 2 -a 0000:29:00.0 -a wq0.0 -a wq0.1 -a wq0.2 -a wq0.3 -- -p 0x1 -q 4 --mac-updating -c hw

6. Send random ip packets with different packet size,includes [64, 128, 256, 512, 1024, 1518] from TG.

7. Check performance from dma app and compare with hw copy test::

    Total packets Tx:                   xxx [pps]
