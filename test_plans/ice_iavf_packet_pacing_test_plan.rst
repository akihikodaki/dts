.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

=============================
ICE IAVF Enable Packet Pacing 
=============================

Description
===========
1. Enable rte_tm to support queue rate limitation configure.
2. Enable devargs to parse the quanta_size for IGP pacing.

The packet pacing quality is heavily rely on FlexRan application/OS setup.
For DPDK validation, we will focus on:
1. Make sure queue rate limitation configuration take effect by measure the bandwidth.
2. Should not exceed the bandwidth that be limited by the DCF.  
3. Not to break anything else.

Prerequisites
=============

Topology
--------
DUT port 0 <----> Tester port 0

Hardware
--------
Supported NICs: Intel® Ethernet 800 Series E810-XXVDA4/E810-CQ

Software
--------
dpdk: http://dpdk.org/git/dpdk
runtime command: https://doc.dpdk.org/guides/testpmd_app_ug/testpmd_funcs.html

General Set Up
--------------
1. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110

2. Get the pci device id and interface of DUT and tester.
   For example, 0000:3b:00.0 and 0000:3b:00.1 is pci device id,
   ens785f0 and ens785f1 is interface::

    <dpdk dir># ./usertools/dpdk-devbind.py -s

    0000:3b:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci
    0000:3b:00.1 'Device 159b' if=ens785f1 drv=ice unused=vfio-pci

3. If vf_num >= 2, Generate 2 VF on PF0, set mac address for VF1::

    # echo 2 > /sys/bus/pci/devices/0000:3b:00.0/sriov_numvfs
    # ip link set dev ens785f0 vf 0 trust on
    # ip link set ens785f0 vf 1 mac 00:11:22:33:44:55

   Else, Generate 1 VF on PF0, set mac address for VF0::

    # echo 1 > /sys/bus/pci/devices/0000:3b:00.0/sriov_numvfs
    # ip link set ens785f0 vf 0 mac 00:11:22:33:44:55

4. Bind the DUT port to dpdk::

    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>

Test Case
=========
Common Steps
------------
TREX sends one stream with frame size 64, mac address is "00:11:22:33:44:55", 100% max rate.
When check the throughput ratio of each queue, stop the forward and check the TX-packets ratio of queues.
The TX-packets ratio of queues is same as TX throughput ratio of queues.

Test Case 1: Without quanta size, check peak_tb_rate
----------------------------------------------------
Launch testpmd without quanta size, check the TX throughput.

Test Steps
~~~~~~~~~~
1. Launch testpmd::

    <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -l 1-4 -n 4 -a 0000:3b:01.0 --file-prefix=tx -- -i 

2. Configure rate limit::

    testpmd> port stop all
    testpmd> add port tm node shaper profile 0 1 1000000 0 612980769 0 0 0 
    testpmd> add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0 
    testpmd> add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    testpmd> add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> port tm hierarchy commit 0 no
    testpmd> port start all
    testpmd> set fwd mac
    testpmd> start

3. Send one stream from TREX.

4. Check the TX throughput of port 0::

    testpmd> show port stats 0

   Check the TX throughput is 612MBps.

Test Case 2: Single queue, check peak_tb_rate
---------------------------------------------
Launch testpmd with quanta_size=1024, check the TX throughput.

Test Steps
~~~~~~~~~~
1. Launch testpmd::

    <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -l 1-4 -n 4 -a 0000:3b:01.0,quanta_size=1024 --file-prefix=tx -- -i 

2. Configure rate limit::

    testpmd> port stop all
    testpmd> add port tm node shaper profile 0 1 1000000 0 612980769 0 0 0 
    testpmd> add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0 
    testpmd> add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    testpmd> add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> port tm hierarchy commit 0 no
    testpmd> port start all
    testpmd> set fwd mac
    testpmd> start

3. Send one stream from TREX.

4. Check the TX throughput of port 0::

    testpmd> show port stats 0

   Check the TX throughput is 612MBps.

Test Case 3: Multi queues, check peak_tb_rate
---------------------------------------------
Launch testpmd with quanta_size=1024 and multi queues, check the TX throughput and the throughput ratio of each queue.

Test Steps
~~~~~~~~~~
1. Launch testpmd with 8 queues::

    <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -l 1-4 -n 4 -a 0000:3b:01.0,quanta_size=1024 --file-prefix=tx -- -i --txq=8 --rxq=8

2. Configure each queue with same rate limit::

    testpmd> port stop all
    testpmd> add port tm node shaper profile 0 1 1000000 0 100000000 0 0 0 
    testpmd> add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0 
    testpmd> add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    testpmd> add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 2 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 3 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 4 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 5 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 6 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 7 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> port tm hierarchy commit 0 no
    testpmd> port start all
    testpmd> set fwd mac
    testpmd> start

3. Send one stream from TREX.

4. Check the TX throughput of port 0::

    testpmd> show port stats 0

   Check the TX throughput is 800MBps.
 
   Check the throughput ratio of each queue::
    
    testpmd> stop

   Check the TX throughput of queue 0-7 is 1:1:1:1:1:1:1:1.

Test Case 4: Modify quanta_size, check peak_tb_rate
---------------------------------------------------
Launch testpmd with quanta_size=4096 and multi queues, check the TX throughput and the throughput ratio of each queue.

Test Steps
~~~~~~~~~~
1. Launch testpmd with 8 queues::

    <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -l 1-4 -n 4 -a 0000:3b:01.0,quanta_size=4096 --file-prefix=tx -- -i --txq=8 --rxq=8

2. Configure each queue with same rate limit::

    testpmd> port stop all
    testpmd> add port tm node shaper profile 0 1 1000000 0 100000000 0 0 0 
    testpmd> add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0 
    testpmd> add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    testpmd> add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 2 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 3 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 4 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 5 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 6 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 7 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> port tm hierarchy commit 0 no
    testpmd> port start all
    testpmd> set fwd mac
    testpmd> start

3. Send one stream from TREX.

4. Check the TX throughput of port 0::

    testpmd> show port stats 0

   Check the TX throughput is 800MBps.
 
   Check the throughput ratio of each queue::
    
    testpmd> stop

   Check the TX throughput of queue 0-7 is 1:1:1:1:1:1:1:1.

Test Case 5: Invalid quanta_size, check peak_tb_rate
----------------------------------------------------
The scope of quanta size is [256, 4096], and it should be the product of 64.
Launch testpmd with quanta_size=1000, check it shows invalid quanta size.

Test Steps
~~~~~~~~~~
1. Launch testpmd::

    <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -l 1-4 -n 4 -a 0000:3b:01.0,quanta_size=1000 --file-prefix=tx -- -i 

2. check it shows invalid quanta size.

Test Case 6: Multi queues with different rate limit, check peak_tb_rate
-----------------------------------------------------------------------
Launch testpmd with quanta_size=1024 and multi queues, then configure each queue with diff rate limit,
check the TX throughput and the throughput ratio of each queue.

Test Steps
~~~~~~~~~~
1. Launch testpmd with 8 queues::

    <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -l 1-4 -n 4 -a 0000:3b:01.0,quanta_size=1024 --file-prefix=tx -- -i --txq=8 --rxq=8

2. Configure each queue with diff rate limit::

    testpmd> port stop all
    testpmd> add port tm node shaper profile 0 1 1000000 0 10000000 0 0 0
    testpmd> add port tm node shaper profile 0 2 1000000 0 20000000 0 0 0
    testpmd> add port tm node shaper profile 0 3 1000000 0 30000000 0 0 0
    testpmd> add port tm node shaper profile 0 4 1000000 0 40000000 0 0 0
    testpmd> add port tm node shaper profile 0 5 1000000 0 50000000 0 0 0
    testpmd> add port tm node shaper profile 0 6 1000000 0 60000000 0 0 0
    testpmd> add port tm node shaper profile 0 7 1000000 0 70000000 0 0 0
    testpmd> add port tm node shaper profile 0 8 1000000 0 80000000 0 0 0
    testpmd> add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0 
    testpmd> add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0
    testpmd> add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 1 900 0 1 2 2 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 2 900 0 1 2 3 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 3 900 0 1 2 4 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 4 900 0 1 2 5 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 5 900 0 1 2 6 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 6 900 0 1 2 7 0 0xffffffff 0 0
    testpmd> add port tm leaf node 0 7 900 0 1 2 8 0 0xffffffff 0 0
    testpmd> port tm hierarchy commit 0 no
    testpmd> port start all
    testpmd> set fwd mac
    testpmd> start

3. Send one stream from TREX.

4. Check the TX throughput of port 0::

    testpmd> show port stats 0

   Check the TX throughput is 360MBps.
 
   Check the throughput ratio of each queue::
    
    testpmd> stop

   Check the TX throughput of queue 0-7 is 1:2:3:4:5:6:7:8.

Test Case 7: Port rate limit less than queue rate limit
-------------------------------------------------------
Launch dcf testpmd with quanta_size=1024 and multi queues, then configure port rate limit less than queue rate limit,
check the TX throughput and the throughput ratio of each queue.

Test Steps
~~~~~~~~~~
1. Launch dcf testpmd with 8 queues::

    <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -l 1-4 -n 4 -a 0000:3b:01.0,cap=dcf -a 3b:01.1,quanta_size=1024 --file-prefix=tx -- -i --txq=8 --rxq=8 --port-topology=loop

2. Configure port rate limit less than queue rate limit::

    testpmd> port stop all
    testpmd> add port tm node shaper profile 0 1 1000000 0 100000000 0 0 0   
    testpmd> add port tm node shaper profile 1 2 1000000 0 612980769 0 0 0   
    testpmd> add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0              
    testpmd> add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0          
    testpmd> add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0         
    testpmd> add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0         
    testpmd> add port tm nonleaf node 1 1000 -1 0 1 0 -1 1 0 0
    testpmd> add port tm nonleaf node 1 900 1000 0 1 1 -1 1 0 0          
    testpmd> add port tm leaf node 1 0 900 0 1 2 2 0 0xffffffff 0 0         
    testpmd> add port tm leaf node 1 1 900 0 1 2 2 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 2 900 0 1 2 2 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 3 900 0 1 2 2 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 4 900 0 1 2 2 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 5 900 0 1 2 2 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 6 900 0 1 2 2 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 7 900 0 1 2 2 0 0xffffffff 0 0
    testpmd> port tm hierarchy commit 0 no
    testpmd> port tm hierarchy commit 1 no  
    testpmd> port start all
    testpmd> set fwd mac
    testpmd> start

3. Send one stream from TREX.

4. Check the TX throughput of port 1::

    testpmd> show port stats 1

   Check the TX throughput is 100MBps.
 
   Check the throughput ratio of each queue::
    
    testpmd> stop

   Check the TX throughput of port1 queue 0-7 is 1:1:1:1:1:1:1:1.

Test Case 8: Port rate limit more than queue rate limit
-------------------------------------------------------
Launch dcf testpmd with quanta_size=1024 and multi queues, then configure port rate limit more than queue rate limit,
check the TX throughput and the throughput ratio of each queue.

Test Steps
~~~~~~~~~~
1. Launch dcf testpmd with 8 queues::

    <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -l 1-4 -n 4 -a 0000:3b:01.0,cap=dcf -a 3b:01.1,quanta_size=1024 --file-prefix=tx -- -i --txq=8 --rxq=8 --port-topology=loop

2. Configure port rate limit more than queue rate limit::

    testpmd> port stop all
    testpmd> add port tm node shaper profile 0 1 1000000 0 200000000 0 0 0   
    testpmd> add port tm node shaper profile 1 2 1000000 0 10000000 0 0 0   
    testpmd> add port tm nonleaf node 0 1000 -1 0 1 0 -1 1 0 0              
    testpmd> add port tm nonleaf node 0 900 1000 0 1 1 -1 1 0 0          
    testpmd> add port tm leaf node 0 0 900 0 1 2 1 0 0xffffffff 0 0         
    testpmd> add port tm leaf node 0 1 900 0 1 2 1 0 0xffffffff 0 0         
    testpmd> add port tm nonleaf node 1 1000 -1 0 1 0 -1 1 0 0
    testpmd> add port tm nonleaf node 1 900 1000 0 1 1 -1 1 0 0          
    testpmd> add port tm leaf node 1 0 900 0 1 2 2 0 0xffffffff 0 0         
    testpmd> add port tm leaf node 1 1 900 0 1 2 2 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 2 900 0 1 2 2 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 3 900 0 1 2 2 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 4 900 0 1 2 2 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 5 900 0 1 2 2 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 6 900 0 1 2 2 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 7 900 0 1 2 2 0 0xffffffff 0 0
    testpmd> port tm hierarchy commit 0 no
    testpmd> port tm hierarchy commit 1 no  
    testpmd> port start all
    testpmd> set fwd mac
    testpmd> start

3. Send one stream from TREX.

4. Check the TX throughput of port 1::

    testpmd> show port stats 1

   Check the TX throughput is 80MBps.
 
   Check the throughput ratio of each queue::
    
    testpmd> stop

   Check the TX throughput of port1 queue 0-7 is 1:1:1:1:1:1:1:1.

